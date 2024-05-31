from django import forms
from .models import City
from telegram_auth.models import ParserSetting
from .models import News
from django_ckeditor_5.widgets import CKEditor5Widget


class ParserForm(forms.ModelForm):
    city = forms.ModelChoiceField(queryset=City.objects.all(), label="Город")

    class Meta:
        model = ParserSetting
        fields = ['city', 'keywords', 'excludes', 'groups']
        widgets = {
            'keywords': forms.HiddenInput(attrs={'id': 'id_keywords'}),
            'excludes': forms.HiddenInput(attrs={'id': 'id_excludes'}),
            'groups': forms.HiddenInput(attrs={'id': 'id_groups'}),
        }


class NewsForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget(config_name='extends'))

    class Meta:
        model = News
        fields = ['title', 'content']
