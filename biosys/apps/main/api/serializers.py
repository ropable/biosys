from __future__ import absolute_import, unicode_literals, print_function, division

import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_gis import serializers as serializers_gis

from main.api.validators import get_record_validator_for_dataset
from main.constants import MODEL_SRID
from main.models import Project, Site, Dataset, Record


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ('password',)


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(required=False)
    centroid = serializers_gis.GeometryField(required=False, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'


class SiteSerializer(serializers.ModelSerializer):
    centroid = serializers_gis.GeometryField(required=False, read_only=True)

    class Meta:
        model = Site
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
    class DataPackageValidator:
        def __init__(self):
            self.dataset_type = Dataset.TYPE_GENERIC

        def __call__(self, value):
            Dataset.validate_data_package(value, self.dataset_type)

        def set_context(self, serializer_field):
            data = serializer_field.parent.context['request'].data
            self.dataset_type = data.get('type')

    data_package = serializers.JSONField(
        validators=[
            DataPackageValidator()
        ]
    )

    class Meta:
        model = Dataset
        fields = '__all__'


class SchemaValidator:
    def __init__(self, strict=True):
        self.strict = strict
        self.dataset = None

    def __call__(self, data):
        if not data:
            msg = "cannot be null or empty"
            raise ValidationError(('data', msg))
        if self.dataset is not None:
            validator = get_record_validator_for_dataset(self.dataset)
            validator.schema_error_as_warning = not self.strict
            result = validator.validate(data)
            if result.has_errors:
                error_messages = ['{col_name}::{message}'.format(col_name=k, message=v) for k, v in
                                  result.errors.items()]
                raise ValidationError(error_messages)

    def set_context(self, serializer_field):
        ctx = serializer_field.parent.context
        if 'dataset' in ctx:
            self.dataset = ctx['dataset']


class RecordSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, **kwargs):
        super(RecordSerializer, self).__init__(instance, **kwargs)
        strict = kwargs.get('context', {}).get('strict', False)
        schema_validator = SchemaValidator(strict=strict)
        self.fields['data'].validators = [schema_validator]
        self.dataset = kwargs.get('context', {}).get('dataset', None)

    @staticmethod
    def get_site(dataset, data, force_create=False):
        schema = dataset.schema
        site_fk = schema.get_fk_for_model('Site')
        site = None
        if site_fk:
            model_field = site_fk.model_field
            site_value = data.get(site_fk.data_field)
            kwargs = {
                "project": dataset.project,
                model_field: site_value
            }
            site = Site.objects.filter(**kwargs).first()
            if site is None and force_create:
                site = Site.objects.create(**kwargs)
        return site

    @staticmethod
    def set_site(instance, validated_data, force_create=False, commit=True):
        site = RecordSerializer.get_site(instance.dataset, validated_data['data'], force_create=force_create)
        if site is not None and instance.site != site:
            instance.site = site
            if commit:
                instance.save()
        return instance

    @staticmethod
    def get_datetime(dataset, data):
        return dataset.schema.cast_record_observation_date(data)

    @staticmethod
    def get_geometry(dataset, data):
        return dataset.schema.cast_geometry(data, default_srid=MODEL_SRID)

    @staticmethod
    def set_date(instance, validated_data, commit=True):
        dataset = instance.dataset
        observation_date = RecordSerializer.get_datetime(dataset, validated_data['data'])
        if observation_date:
            # convert to datetime with timezone awareness
            if isinstance(observation_date, datetime.date):
                observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
            tz = dataset.project.timezone or timezone.get_current_timezone()
            observation_date = timezone.make_aware(observation_date, tz)
            instance.datetime = observation_date
            if commit:
                instance.save()
        return instance

    @staticmethod
    def set_geometry(instance, validated_data, commit=True):
        geom = RecordSerializer.get_geometry(instance.dataset, validated_data['data'])
        if geom:
            instance.geometry = geom
            if commit:
                instance.save()
        return instance

    def set_date_and_geometry(self, instance, validated_data, commit=True):
        self.set_date(instance, validated_data, commit=commit)
        self.set_geometry(instance, validated_data, commit=commit)
        return instance

    @staticmethod
    def get_species_name(dataset, data):
        return dataset.schema.cast_species_name(data)

    @classmethod
    def set_species_name(cls, instance, validated_data, commit=True):
        species_name = cls.get_species_name(instance.dataset, validated_data['data'])
        if species_name:
            instance.species_name = species_name
            if commit:
                instance.save()
        return instance

    def get_name_id(self, species_name):
        name_id = -1
        if 'species_mapping' in self.context and species_name:
            name_id = int(self.context['species_mapping'].get(species_name, -1))
        return name_id

    def set_name_id(self, instance, commit=True):
        name_id = self.get_name_id(instance.species_name)
        instance.name_id = name_id
        if commit:
            instance.save()
        return instance

    def set_species_name_and_id(self, instance, validated_data, commit=True):
        self.set_species_name(instance, validated_data, commit=commit)
        self.set_name_id(instance, commit=commit)
        return instance

    def set_fields_from_data(self, instance, validated_data):
        instance = self.set_site(instance, validated_data)
        if self.dataset and self.dataset.type in [Dataset.TYPE_OBSERVATION, Dataset.TYPE_SPECIES_OBSERVATION]:
            instance = self.set_date_and_geometry(instance, validated_data)
            if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                instance = self.set_species_name_and_id(instance, validated_data)
        return instance

    def create(self, validated_data):
        """
        Extract the Site from data if not specified
        :param validated_data:
        :return:
        """
        instance = super(RecordSerializer, self).create(validated_data)
        return self.set_fields_from_data(instance, validated_data)

    def update(self, instance, validated_data):
        instance = super(RecordSerializer, self).update(instance, validated_data)
        # case of a patch where the dataset is not sent
        self.dataset = self.dataset or instance.dataset
        return self.set_fields_from_data(instance, validated_data)

    class Meta:
        model = Record
        fields = '__all__'
