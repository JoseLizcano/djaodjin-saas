# Copyright (c) 2016, DjaoDjin inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from .utils import get_roles, get_organization_model


class OrganizationMixinBase(object):
    """
    Returns an ``Organization`` from a URL.
    """

    organization_url_kwarg = 'organization'

    @staticmethod
    def attached_manager(organization):
        # defer call to ``get_user_model`` so that we can import this module
        # in django.conf.settings.
        from . import settings
        managers = get_user_model().objects.filter(
            pk__in=get_roles(settings.MANAGER).filter(
            organization=organization).values('user'))
        if managers.count() == 1:
            manager = managers.get()
            if organization.slug == manager.username:
                return manager
        return None

    def get_organization(self):
        return get_object_or_404(get_organization_model(),
            slug=self.kwargs.get(self.organization_url_kwarg))

    def get_url_kwargs(self):
        """
        Rebuilds the ``kwargs`` to pass to ``reverse()``.
        """
        url_kwargs = {}
        if 'organization' in self.kwargs:
            url_kwargs.update({'organization': self.kwargs['organization']})
        return url_kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganizationMixinBase, self).get_context_data(**kwargs)
        organization = self.organization
        context.update({'organization': organization})
        # XXX These might be moved to a higher-level
        urls_default = {
            'api_cart': reverse('saas_api_cart'),
            'api_redeem': reverse('saas_api_redeem_coupon'),
        }
        if 'urls' in context:
            context['urls'].update(urls_default)
        else:
            context.update({'urls': urls_default})

        # URLs for both sides (subscriber and provider).
        urls_organization = {
            'api_base': reverse('saas_api_organization', args=(organization,)),
            'api_card': reverse('saas_api_card', args=(organization,)),
            'api_profile_base': reverse('saas_api_profile'),
            'api_subscriptions': reverse(
                'saas_api_subscription_list', args=(organization,)),
            'profile_base': reverse('saas_profile'),
            'profile': reverse(
                'saas_organization_profile', args=(organization,)),
            'billing': reverse('saas_billing_info', args=(organization,)),
            'subscriptions': reverse(
                'saas_subscription_list', args=(organization,)),
        }
        if self.attached_manager(self.organization):
            urls_organization.update({
                'password_change': reverse(
                    'password_change', args=(organization.slug,))})
        else:
            urls_organization.update({
                'managers': reverse('saas_role_list',
                    args=(organization, 'managers')),
                'contributors': reverse('saas_role_list',
                    args=(organization, 'contributors'))})
        if 'urls' in context:
            if 'organization' in context['urls']:
                context['urls']['organization'].update(urls_organization)
            else:
                context['urls'].update({'organization': urls_organization})
        else:
            context.update({'urls': {'organization': urls_organization}})

        if organization.is_provider:
            provider = organization
            urls_provider = {
                'api_bank': reverse('saas_api_bank', args=(provider,)),
                'api_coupons': reverse(
                    'saas_api_coupon_list', args=(provider,)),
                'api_metrics_coupons': reverse(
                    'saas_metrics_coupons', args=(provider,)),
                'api_metrics_plans': reverse(
                    'saas_api_metrics_plans', args=(provider,)),
                'api_plans': reverse('saas_api_plans', args=(provider,)),
                'api_subscribers_active': reverse(
                    'saas_api_subscribed', args=(provider,)),
                'api_subscribers_churned': reverse(
                    'saas_api_churned', args=(provider,)),
                'api_users': reverse('saas_api_user_list'),
                'api_users_registered': reverse('saas_api_registered'),
                'profile': reverse('saas_provider_profile'),
                'coupons': reverse('saas_coupon_list', args=(provider,)),
                'dashboard': reverse('saas_dashboard', args=(provider,)),
                'metrics_sales': reverse(
                    'saas_metrics_summary', args=(provider,)),
                'metrics_plans': reverse(
                    'saas_metrics_plans', args=(provider,)),
                'subscribers': reverse(
                    'saas_subscriber_list', args=(provider,)),
                'transfers': reverse(
                    'saas_transfer_info', args=(provider,)),
            }
            if 'urls' in context:
                if 'provider' in context['urls']:
                    context['urls']['provider'].update(urls_provider)
                else:
                    context['urls'].update({'provider': urls_provider})
            else:
                context.update({'urls': {'provider': urls_provider}})

        return context

    @property
    def organization(self):
        if not hasattr(self, '_organization'):
            self._organization = self.get_organization()
        return self._organization
