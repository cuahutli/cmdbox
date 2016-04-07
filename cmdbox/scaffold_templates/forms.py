from django import forms
from django.utils.translation import ugettext_lazy as _

from cmdbox.scaffold_templates.models import ScaffoldTemplate
from cmdbox.core.forms import AbstractServiceCreateForm


class CreateScaffoldTemplate(AbstractServiceCreateForm):
    description = forms.CharField(
        label=_('Description'),
        max_length=100,
        help_text=_('Give a brief description of what this scaffold template is about. Not required.'),
        required=False
    )

    class Meta(AbstractServiceCreateForm.Meta):
        model = ScaffoldTemplate


class EditScaffoldTemplate(forms.ModelForm):
    class Meta:
        model = ScaffoldTemplate
        fields = '__all__'
