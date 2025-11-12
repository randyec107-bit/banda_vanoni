from django import forms
from .models import Adquisicion

class AdquisicionForm(forms.ModelForm):
    fecha_arribo = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})  
    )

    class Meta:
        model = Adquisicion
        fields = "__all__"
