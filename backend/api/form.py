from django import forms

from users.models import Subscribe


class RequiredInlineFormSet(forms.models.BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        form.empty_permitted = False
        return form


class SubcribeForm(forms.ModelForm):
    class Meta:
        model = Subscribe
        fields = "__all__"

    def clean(self):
        data = self.cleaned_data
        if data["user"] == data["author"]:
            raise forms.ValidationError("Нельзя подписаться на самого себя")