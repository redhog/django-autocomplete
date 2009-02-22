# coding=utf8
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words

from django.contrib import admin
from django.db import models

import operator
from django.contrib.auth.models import Message
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str

class ForeignKeySearchInput(forms.HiddenInput):
	"""
	A Widget for displaying ForeignKeys in an autocomplete search input 
	instead in a <select> box.
	"""
	class Media:
		css = {
			'all': ('jquery.autocomplete.css',)
		}
		js = (
			'js/jquery.js',
			'js/jquery.autocomplete.js'
		)

	def label_for_value(self, value):
		key = self.rel.get_related_field().name
		obj = self.rel.to._default_manager.get(**{key: value})
		return truncate_words(obj, 14)

	def __init__(self, rel, search_fields, attrs=None):
		self.rel = rel
		self.search_fields = search_fields
		super(ForeignKeySearchInput, self).__init__(attrs)

	def render(self, name, value, attrs=None):
		if attrs is None:
			attrs = {}
		rendered = super(ForeignKeySearchInput, self).render(name, value, attrs)
		if value:
			label = self.label_for_value(value)
		else:
			label = u''
		return rendered + mark_safe(u'''
<input type="text" id="lookup_%(name)s" value="%(label)s" size="40"/>
<script type="text/javascript">
$(document).ready(function(){

function liFormat_%(name)s (row, i, num) {
	var result = row[0] ;
	return result;
}
function selectItem_%(name)s(li) {
	if( li == null ) var sValue = '';
	if( !!li.extra ) var sValue = li.extra[0];
	else var sValue = li.selectValue;
	$("#id_%(name)s").val( sValue );
}

// --- Автозаполнение ---
$("#lookup_%(name)s").autocomplete("../search/", {
		extraParams: {
		search_fields: '%(search_fields)s',
		app_label: '%(app_label)s',
		model_name: '%(model_name)s',
	},
	delay:10,
	minChars:2,
	matchSubset:1,
	autoFill:true,
	matchContains:1,
	cacheLength:10,
	selectFirst:true,
	formatItem:liFormat_%(name)s,
	maxItemsToShow:10,
	onItemSelect:selectItem_%(name)s
}); 
// --- Автозаполнение ---
});
</script>

		''') % {
			'search_fields': ','.join(self.search_fields),
			'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
			'model_name': self.rel.to._meta.module_name,
			'app_label': self.rel.to._meta.app_label,
			'label': label,
			'name': name,
			'value': value,
		}


class ManyToManySearchInput(forms.MultipleHiddenInput):
	"""
	A Widget for displaying ForeignKeys in an autocomplete search input 
	instead in a <select> box.
	"""
	class Media:
		css = {
			'all': ('jquery.autocomplete.css',)
		}
		js = (
			'js/jquery.js',
			'js/jquery.autocomplete.js'
		)

	def __init__(self, rel, search_fields, attrs=None):
		self.rel = rel
		self.search_fields = search_fields
		super(ManyToManySearchInput, self).__init__(attrs)
		self.help_text = ''

	def render(self, name, value, attrs=None):
		if attrs is None:
			attrs = {}

		label = ''
		selected = ''
		for id in value:
			obj = self.rel.to.objects.get(id=id)

			selected = selected + mark_safe(u"""
				<div class="to_delete" >
					<img src="/media/common/admin_media/img/admin/icon_deletelink.gif"/> 
					<input type="hidden" name="%(name)s" value="%(value)s"/>
					%(label)s
				</div>""" 
				)%{
					'label': obj.name,
					'name': name,
					'value': obj.id,
			}

		
		return mark_safe(u'''
<input type="text" id="lookup_%(name)s" value="" size="40"/>%(label)s

<div id="box_%(name)s" style="float:left; padding-left:120px; width:300px; cursor:pointer;">
	%(selected)s
</div>

<script type="text/javascript">
$(document).ready(function(){

	function liFormat_%(name)s (row, i, num) {
		var result = row[0] ;
		return result;
	}
	function selectItem_%(name)s(li) {
		if( li == null ) return

		// --- Создаю новый элемент ---
		$('<div class="to_delete" ><img src="/media/common/admin_media/img/admin/icon_deletelink.gif"/> <input type="hidden" name="%(name)s" value="'+li.extra[0]+'"/>'
			+li.selectValue
			+'</div>'
		)
		.click(function () {$(this).remove();})
		.appendTo("#box_%(name)s");

		$("#lookup_%(name)s").val( '' );
	}
	
	// --- Автозаполнение ---
	$("#lookup_%(name)s").autocomplete("../search/", {
			extraParams: {
			search_fields: '%(search_fields)s',
			app_label: '%(app_label)s',
			model_name: '%(model_name)s',
		},
		delay:10,
		minChars:2,
		matchSubset:1,
		autoFill:false,
		matchContains:1,
		cacheLength:10,
		selectFirst:true,
		formatItem:liFormat_%(name)s,
		maxItemsToShow:10,
		onItemSelect:selectItem_%(name)s
	}); 
// --- удаление изначально выбраных элементов ---
	$(".to_delete").click(function () {$(this).remove();});
});
</script>

		''') % {
			'search_fields': ','.join(self.search_fields),
			'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
			'model_name': self.rel.to._meta.module_name,
			'app_label': self.rel.to._meta.app_label,
			'label': label,
			'name': name,
			'value': value,
			'selected':selected,
		}

class AutocompleteModelAdmin(admin.ModelAdmin):
	def __call__(self, request, url):
		if url is None:
			pass
		elif url == 'search':
			return self.search(request)
		return super(AutocompleteModelAdmin, self).__call__(request, url)

	def search(self, request):
		
		#	Searches in the fields of the given related model and returns the 
		#	result as a simple string to be used by the jQuery Autocomplete plugin
		
		query = request.GET.get('q', None)  # не забудь убрать это виндозное шаманство!!!

		app_label = request.GET.get('app_label', None)
		model_name = request.GET.get('model_name', None)
		search_fields = request.GET.get('search_fields', None)

		#print '-----------------------'
		#print search_fields, app_label, model_name, query
		
		if search_fields and app_label and model_name and query:
			def construct_search(field_name):
				# use different lookup methods depending on the notation
				if field_name.startswith('^'):
					return "%s__istartswith" % field_name[1:]
				elif field_name.startswith('='):
					return "%s__iexact" % field_name[1:]
				elif field_name.startswith('@'):
					return "%s__search" % field_name[1:]
				else:
					return "%s__icontains" % field_name

			model = models.get_model(app_label, model_name)
			q = None
			for field_name in search_fields.split(','):
				name = construct_search(field_name)
				#print name,'=',query
				if q:
					q = q | models.Q( **{str(name):query} )
				else:
					q = models.Q( **{str(name):query} )
			#print 'q = ', q
			qs = model.objects.filter( q )
			#print 'qs = ', qs
			
			data = ''.join([u'%s|%s\n' % (f.__unicode__(), f.pk) for f in qs])
			return HttpResponse(data)
		return HttpResponseNotFound()

	def formfield_for_dbfield(self, db_field, **kwargs):
		#	Overrides the default widget for Foreignkey fields if they are
		#	specified in the related_search_fields class attribute.
		if isinstance(db_field, models.ForeignKey) and \
				db_field.name in self.related_search_fields:
			kwargs['widget'] = ForeignKeySearchInput(db_field.rel,
									self.related_search_fields[db_field.name])
		
		if isinstance(db_field, models.ManyToManyField)and \
				db_field.name in self.related_search_fields:
			kwargs['widget'] = ManyToManySearchInput(db_field.rel,
									self.related_search_fields[db_field.name])
			db_field.help_text = ''

		return super(AutocompleteModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)
