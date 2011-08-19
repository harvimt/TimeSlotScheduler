/*
 * Admin Weights Javascript/JQuery File
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * See templates/admin_weights.html
 *
 * :Copyright © 2011 Mark Harviston <infinull@gmail.com>
 */
$(document).ready(function(){
	$("#pref_type_tmpl").template('pref_type');
	$("#pref_weight_tmpl").template('pref_weight');
	var pref_type_list = $('#pref_type_list')
	var add_pref_type_btn_click, del_pref_type_btn_click, add_weight_btn_click, del_weight_btn_click;

	add_pref_type_btn_click = function(){
		var new_pref_type = $.tmpl('pref_type', {index: pref_type_list.children('dl').length});

		new_pref_type.find('.del_pref_type_btn').click(del_pref_type_btn_click)
		new_pref_type.find('.add_weight_btn').click(add_weight_btn_click)

		new_pref_type.appendTo(pref_type_list)
	};
	del_pref_type_btn_click = function(){
		var to_del = $(this).parent();
		var to_dec = to_del.nextAll();
		to_del.remove()
		to_dec.each(function(x,e){
			var index = $(e).index()
			$(e).find('input').each(function(y,i){
				$(i).attr('name',$(i).attr('name').replace(/^\d+_/,index + '_'))
			});
		});
	};
	add_weight_btn_click = function(){
		var weights_list = $(this).parent().children('.weights_list');
		var pt_index = $(this).parent().parent().index() - 1;
		var wt_index = weights_list.children().length;
		var new_weight = $.tmpl('pref_weight', {pt_index:pt_index,wt_index:wt_index});

		new_weight.find('.del_weight_btn').click(del_weight_btn_click)
		new_weight.appendTo(weights_list)
	};
	del_weight_btn_click = function(){
		var to_del = $(this).parent();
		var to_dec = to_del.nextAll();
		to_del.remove();
		to_dec.find('input').each(function(x,i){
			var index = $(i).parent().index()
			var new_name = $(i).attr('name').replace(/_weights_\d+_/,'_weights_'+index+'_')
			$(i).attr('name', new_name);
		});
	};

	$("#add_pref_type_btn").click(add_pref_type_btn_click);
	$('.del_pref_type_btn').click(del_pref_type_btn_click);
	$('.add_weight_btn').click(add_weight_btn_click);
	$('.del_weight_btn').click(del_weight_btn_click);
});

