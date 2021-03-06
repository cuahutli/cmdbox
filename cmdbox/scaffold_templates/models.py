from __future__ import unicode_literals
import os.path
import re

import humanize

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from cmdbox.core.models import AbstractService
from cmdbox.scaffold_templates.validators import validate_folder


class ScaffoldTemplate(AbstractService):

    class Meta:
        verbose_name = _('scaffold template')
        verbose_name_plural = _('scaffold template')
        unique_together = (('user', 'slug'), )
        ordering = ('-updated_at', )

    def get_folders_dict(self):
        folder_set = self.files.filter(file_type=File.FOLDER).values()
        folders = dict()
        for folder in folder_set:
            folders[folder['id']] = folder
        return folders

    def list_files(self):
        folders = self.get_folders_dict()
        files = self.files.filter(file_type=File.FILE).select_related('folder')
        for _file in files:
            _file.build_path(folders)
        files = list(files)
        files.sort(key=lambda k: (os.path.dirname(k.path), os.path.basename(k.path)))
        return files


class File(models.Model):
    FILE = 1
    FOLDER = 2
    FILE_TYPES = (
        (FILE, _('file')),
        (FOLDER, _('folder'))
    )

    name = models.CharField(_('name'), max_length=255)
    extension = models.CharField(_('extension'), max_length=10, null=True, blank=True)
    size = models.PositiveIntegerField(_('size'), default=0)
    template = models.ForeignKey(ScaffoldTemplate, related_name='files')
    folder = models.ForeignKey('File', null=True, related_name='files', validators=[validate_folder, ])
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    file_type = models.PositiveSmallIntegerField(_('file type'), choices=FILE_TYPES, default=FILE)
    content = models.TextField(_('content'), null=True, blank=True)

    class Meta:
        ordering = ('-file_type', 'name', )
        verbose_name = _('file')
        verbose_name_plural = _('files')
        unique_together = (('template', 'folder', 'name'), )

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file_type == File.FILE:
            self.extension = os.path.splitext(self.name)[1][1:].strip()[:10]
            self.calculate_size()
        else:
            self.extension = None
            self.content = None
        super(File, self).save(*args, **kwargs)

    def build_path(self, folders=None):
        if folders is None:
            folders = self.template.get_folders_dict()
        path = '{0}/{1}'.format(self.template.slug, self.name)
        depth = 0
        folder = self.folder
        if folder is not None:
            folder_id = folder.pk
            path = '{0}/{1}'.format(folders[folder_id]['name'], path)
            depth += 1
            while folders[folder_id]['folder_id'] is not None:
                folder_id = folders[folder_id]['folder_id']
                path = '{0}/{1}'.format(folders[folder_id]['name'], path)
                depth += 1
        self.path = path
        self.depth = depth
        return self.path

    def calculate_size(self):
        if self.content:
            self.size = len(self.content.encode('utf8'))
        else:
            self.size = 0

    def get_naturalsize(self):
        return humanize.naturalsize(self.size)

    def is_folder(self):
        return self.file_type == File.FOLDER

    def _get_name_parts(self):
        name, extension = os.path.splitext(self.name)
        if extension == '.' or len(extension) > 11 or re.compile(r'\s').search(extension):
            return (self.name, '')
        return (name, extension)

    def _cut_multiple_copy(self, base_name, copy_text):
        regex = copy_text + '[\s\d+]*$'
        m = re.compile(regex)
        search_result = m.search(base_name)
        if search_result:
            copy_part = search_result.group()
            return base_name[:-len(copy_part) - 1]
        return base_name

    def _generate_duplicate_name(self):
        base_name, extension = self._get_name_parts()
        base_copy_text = _('copy')
        base_name = self._cut_multiple_copy(base_name, base_copy_text)

        copy_text = ' {0}'.format(base_copy_text)
        copy_name = ''

        if base_name.endswith(copy_text):
            base_name = base_name[:-len(copy_text)]

        copy_number = 1
        while True:
            max_length = 255 - len(copy_text) - len(extension)
            copy_name = '{0}{1}{2}'.format(base_name[:max_length], copy_text, extension)

            if File.objects.filter(name=copy_name, template=self.template, folder=self.folder).exists():
                copy_number += 1
                copy_text = ' {0} {1}'.format(base_copy_text, copy_number)
            else:
                break

        self.name = copy_name

    def clone(self):
        new_file = File(
            name=self.name,
            extension=self.extension,
            size=self.size,
            template=self.template,
            folder=self.folder,
            file_type=self.file_type,
            content=self.content
        )
        return new_file

    def duplicate(self):
        with transaction.atomic():
            copy = self.clone()
            copy._generate_duplicate_name()
            copy.save()
            if copy.is_folder():
                template_files = self.template.files.select_related('folder').all()
                files_bulk = duplicate_files(template_files, self, copy)
                if files_bulk:
                    File.objects.bulk_create(files_bulk)
            return copy


def duplicate_files(files, old_folder, new_folder):
    children_files = filter(lambda f: f.folder == old_folder, files)
    files_bulk = list()
    if children_files:
        for old_file in children_files:
            new_file = old_file.clone()
            new_file.folder = new_folder
            if old_file.is_folder():
                new_file.save()
                files_bulk += duplicate_files(files, old_file, new_file)
            else:
                files_bulk.append(new_file)
    return files_bulk
