# -*- coding: utf-8 -*-
from postmonkey import PostMonkey
from collective.mailchimp.interfaces import IMailchimpSettings
from plone.registry.interfaces import IRegistry
import unittest2 as unittest
from plone.testing.z2 import Browser
from plone.app.testing import TEST_USER_ID
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import setRoles
from zope.component import getUtility, getMultiAdapter
from zope.site.hooks import setHooks

from plone.portlets.interfaces import IPortletType
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletDataProvider
from plone.portlets.interfaces import IPortletRenderer

from plone.app.portlets.storage import PortletAssignmentMapping

from collective.mailchimp.portlets import mailchimp as mailchimp
from collective.mailchimp.testing import \
    COLLECTIVE_MAILCHIMP_INTEGRATION_TESTING


class TestPortlet(unittest.TestCase):

    layer = COLLECTIVE_MAILCHIMP_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        setHooks()

    def testPortletTypeRegistered(self):
        portlet = getUtility(IPortletType, name='portlet.MailChimp')
        self.assertEquals(portlet.addview, 'portlet.MailChimp')

    def testInterfaces(self):
        portlet = mailchimp.Assignment(name="foo")
        self.failUnless(IPortletAssignment.providedBy(portlet))
        self.failUnless(IPortletDataProvider.providedBy(portlet.data))

    def testInvokeAddview(self):
        portlet = getUtility(IPortletType, name='portlet.MailChimp')
        mapping = self.portal.restrictedTraverse(
            '++contextportlets++plone.leftcolumn')
        for m in mapping.keys():
            del mapping[m]
        addview = mapping.restrictedTraverse('+/' + portlet.addview)
        addview.createAndAdd(data={})

        self.assertEquals(len(mapping), 1)
        self.failUnless(isinstance(mapping.values()[0], mailchimp.Assignment))

    def testInvokeEditView(self):
        mapping = PortletAssignmentMapping()
        request = self.portal.REQUEST

        mapping['foo'] = mailchimp.Assignment(name="foo")
        editview = getMultiAdapter((mapping['foo'], request), name='edit')
        self.failUnless(isinstance(editview, mailchimp.EditForm))

    def testRenderer(self):
        context = self.portal
        request = self.portal.REQUEST
        view = self.portal.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager,
            name='plone.leftcolumn', context=self.portal)
        assignment = mailchimp.Assignment(name="foo")

        renderer = getMultiAdapter(
            (context, request, view, manager, assignment),
            IPortletRenderer)
        self.failUnless(isinstance(renderer, mailchimp.Renderer))


class TestRenderer(unittest.TestCase):

    layer = COLLECTIVE_MAILCHIMP_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        setHooks()
        # Make sure News Items use simple_publication_workflow
        self.portal.portal_workflow.setChainForPortalTypes(
            ['News Item'], ['simple_publication_workflow'])

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.portal
        request = request or self.portal.REQUEST
        view = view or self.portal.restrictedTraverse('@@plone')
        manager = manager or getUtility(IPortletManager,
            name='plone.leftcolumn',
            context=self.portal)
        assignment = assignment or mailchimp.Assignment(
            template='portlet_recent',
            macro='portlet')

        return getMultiAdapter(
            (context, request, view, manager, assignment),
            IPortletRenderer)


class TestPortletIntegration(unittest.TestCase):

    layer = COLLECTIVE_MAILCHIMP_INTEGRATION_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal_url = self.portal.absolute_url()

        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader('Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_postmonkey_mocker(self):
        from postmonkey import PostMonkey
        mailchimp = PostMonkey(u"abc")
        self.assertEqual(mailchimp.lists(), {
            u'total': 2,
            u'data': [
                {
                    u'id': 625,
                    u'web_id': 625,
                    u'name': u'ACME Newsletter',
                    u'default_from_name': u'info@acme.com',
                },
                {
                    u'id': 626,
                    u'web_id': 626,
                    u'name': u'ACME Newsletter 2',
                    u'default_from_name': u'info@acme.com',
                }
            ]
        })

    def test_add_portlet_form(self):
        self.browser.open(self.portal_url +
            "/++contextportlets++plone.leftcolumn/+/portlet.MailChimp")

        open('/tmp/testbrowser.html', 'w').write(self.browser.contents)
#        import pdb; pdb.set_trace()

        self.assertTrue("Add MailChimp Portlet" in self.browser.contents)
        self.assertTrue("Title" in self.browser.contents)
        self.assertTrue("Available lists" in self.browser.contents)
        self.assertTrue("ACME Newsletter" in self.browser.contents)
        self.assertTrue("ACME Newsletter 2" in self.browser.contents)

    def test_add_portlet(self):
        self.browser.open(self.portal_url +
            "/++contextportlets++plone.leftcolumn/+/portlet.MailChimp")
        self.browser.getControl("Title").value = "ACME Newsletter Portlet"

        self.browser.getControl(
            name="form.widgets.available_lists:list", index=0).value = ["625"]
        #self.browser.getControl(name="form.widgets.available_lists:list")\
        #    .controls[0].click()
        self.browser.getControl("Save").click()

        #self.assertEqual(self.browser.url,
        #    self.portal_url + '/@@manage-portlets')
        #self.assertTrue("ACME Newsletter Portlet" in self.browser.contents)

    def test_edit_portlet(self):
        pass
        #self.browser.open(self.portal_url +
        #    "/++contextportlets++plone.leftcolumn/mailchimp/edit")

    def test_view_portlet(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
