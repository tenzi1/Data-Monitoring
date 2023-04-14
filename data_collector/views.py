from django.shortcuts import render
from django.forms import modelform_factory
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, View, DeleteView
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from .models import DataPoint, Alert
from .forms import AlertForm 

class RecordDataApiView(View):
    def post(self, request, *args, **kwargs):
        if request.META.get('HTTP_AUTH_SECRET') != 'supersecretkey':
            return HttpResponseForbidden('Auth key incorrect')
        form_class = modelform_factory(DataPoint, fields=['node_name', 'data_type', 'data_value'])
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()

class StatusView(TemplateView):
    template_name = 'status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alerts = Alert.objects.filter(is_active=True)
        nodes_and_data_types = DataPoint.objects.all().values('node_name','data_type').distinct()
        status_data_dict = dict()
        for node_and_data_type_pair in nodes_and_data_types:
            node_name = node_and_data_type_pair['node_name']
            data_type = node_and_data_type_pair['data_type']
            latest_data_point = DataPoint.objects.filter(node_name=node_name, data_type=data_type).latest('datetime')
            latest_data_point.has_alert = self.does_have_alert(latest_data_point, alerts)
            data_point_map = status_data_dict.setdefault(node_name, dict())
            data_point_map[data_type] = latest_data_point
        context['status_data_dict'] = status_data_dict
        return context 


    def does_have_alert(self, data_point, alerts):
        for alert in alerts:
            if alert.node_name and data_point.node_name != alert.node_name:
                continue
            if alert.data_type != data_point.data_type:
                continue
            if alert.min_value is not None and data_point.data_value < alert.min_value:
                return True
            if alert.max_value is not None and data_point.data_value > alert.max_value:
                return True
            return False

class AlertListView(ListView):
    model = Alert
    template_name = 'alert_list.html'


class NewAlertView(CreateView):
    template_name = 'create_or_update_alert.html'
    model = Alert
    fields = ('data_type', 'min_value', 'max_value', 'node_name', 'is_active')

    def get_success_url(self):
        return reverse('alerts-list')


class EditAlertView(UpdateView):
    model = Alert
    template_name = 'create_or_update_alert.html'
    fields = ('data_type', 'min_value', 'max_value', 'node_name', 'is_active')

    def get_success_url(self):
        return reverse('alerts-list')


class DeleteAlertView(DeleteView):
    template_name = 'delete_alert.html'
    model = Alert

    def get_success_url(self):
        return reverse('alerts-list')

