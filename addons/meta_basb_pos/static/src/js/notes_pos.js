odoo.define('meta_basb_pos.notes_pos', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PopupWidget = require('point_of_sale.popups');
    var _t = core._t;
    var models = require('point_of_sale.models');


    var PosModelSuper = models.PosModel;

    models.load_fields("res.partner", ["last_purchase_date","last_purchase_diseases","special_access_for_purchase","personal_number","child_ids","relation","relation_string","dasb","beneficiary_number",]);

    models.load_models({
        model: 'disease.purchase.date',
        fields: ['disease_name','partner_name','last_purchase_date','disease_id','partner_id'],
        domain: null,
        loaded: function(self, disease_purchase_date){
            self.disease_purchase_date = disease_purchase_date;
        },
    });
    models.load_models({
        model: 'product.purchase.date',
        fields: ['disease_name','partner_name','last_purchase_date','product_id','partner_id'],
        domain: null,
        loaded: function(self, product_purchase_date){
            self.product_purchase_date = product_purchase_date;
        },
    });

    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            var res = PosModelSuper.prototype.initialize.apply(this, arguments);
            return res;
        },
    });

    screens.ActionpadWidget.include(({
        
        validation_function: function(){
            self = this;
            this._super();
            var order = self.pos.get_order();
            var orderline = order.orderlines.models;
            var is_validation_ok = true;

            // This is for product stock validation
            for (var i=0;i<orderline.length;i++)
            {
                var line = orderline[i];
                var message = '';
                if (line.product.qty_available < line.quantity)
                {
                    message = message +line.product.display_name + ' has only ' + line.product.qty_available + ' unit(s) Available. Your are trying to sale '+ line.quantity + " unit(s)";
                    self.gui.show_popup('error',{
                        'title': _t('Alert!!!!!!!!'),
                        'body':  _t(message),
                    });
                    is_validation_ok = false;
                    break;
                }
            }

            // This is for Guest Customer validation
            if(!order.attributes.client & is_validation_ok)
            {
                var orderline = this.pos.get_order().get_orderlines();
                var product_wise_purchase_list = this.pos.product_purchase_date;
                console.error(orderline);
                console.error(product_wise_purchase_list);

                self.gui.show_popup('error',{
                    'title': _t('Alert!!!!!!!!'),
                    'body':  _t("Please Select Customer."),
                });
                is_validation_ok = false;
            }

            // Restriction for 30 days and 15 days for disease and normal product for purchasing respectively
            if(is_validation_ok)
            {
                //this.pos.push_order(); //this.pos.load_server_data(); 
                var order = this.pos.get_order();
                var orderline = this.pos.get_order().get_orderlines();
                
                // var last_purchase_date = order.attributes.client.last_purchase_date;
                // var last_purchase_diseases = order.attributes.client.last_purchase_diseases;
                var client_id = order.attributes.client.id;

                var idx;
                var result="";
                var disease_wise_purchase_list = this.pos.disease_purchase_date;
                var product_wise_purchase_list = this.pos.product_purchase_date;             

                if (order.attributes.client.special_access_for_purchase == false){
                    for(idx=0; idx<orderline.length; idx++){
                        if (orderline[idx].note){
                            var cr_notes = orderline[idx].note;
                            var current_notes = cr_notes.split(", ");
                            var i;
                            for (i=0; i<current_notes.length; i++){
                                var j;
                                for (j=0; j<disease_wise_purchase_list.length; j++){
                                    if(disease_wise_purchase_list[j].partner_id[0] == client_id)
                                    {
                                        if(disease_wise_purchase_list[j].disease_id[1] == current_notes[i])
                                        {
                                            var today = new Date();
                                            var dt2 = new Date(today);
                                            var dt1 = new Date(disease_wise_purchase_list[j].last_purchase_date);
                                            var date_diff_in_days = Math.floor((Date.UTC(dt2.getFullYear(), dt2.getMonth(), dt2.getDate()) - Date.UTC(dt1.getFullYear(), dt1.getMonth(), dt1.getDate()) ) /(1000 * 60 * 60 * 24));
                                        
                                            var day_limit = parseInt(self.pos.config.day_limit);

                                            if (date_diff_in_days < day_limit){
                                                result = "This Customer [ " + order.attributes.client.name + " ] have already bought medicine for these chronic diseases [ " + current_notes[i] + " ] on " + disease_wise_purchase_list[j].last_purchase_date +". He/She can receive it after "+ (day_limit-date_diff_in_days) + " days";
                                                this.gui.show_popup('error',{
                                                    'title': _t('Alert!!!!!!!!'),
                                                    'body':  _t(result),
                                                });
                                                is_validation_ok = false;
                                                break;
                                            }
                                        }
                                    }
                                }
                                if (!is_validation_ok)
                                    break;
                            }
                            
                        }
                        /* disabled this functions
                        else{
                            for (var jj=0; jj<product_wise_purchase_list.length; jj++){
                                if(product_wise_purchase_list[jj].partner_id[0] == client_id)
                                {
                                    if(product_wise_purchase_list[jj].product_id[0] == orderline[idx].product.id)
                                    {
                                        var today = new Date();
                                        var dt2 = new Date(today);
                                        var dt1 = new Date(product_wise_purchase_list[jj].last_purchase_date);
                                        var date_diff_in_days = Math.floor((Date.UTC(dt2.getFullYear(), dt2.getMonth(), dt2.getDate()) - Date.UTC(dt1.getFullYear(), dt1.getMonth(), dt1.getDate()) ) /(1000 * 60 * 60 * 24));
                                    

                                        if (date_diff_in_days < 15){
                                            result = "This Customer [ " + order.attributes.client.name + " ] have already buy medicine [ "+ product_wise_purchase_list[jj].product_id[1] +" ] on " + product_wise_purchase_list[jj].last_purchase_date +". He/She can receive it after "+ (15-date_diff_in_days) + " days";
                                            this.gui.show_popup('error',{
                                                'title': _t('Alert!!!!!!!!'),
                                                'body':  _t(result),
                                            });
                                            is_validation_ok = false;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                        */
                        if (!is_validation_ok)
                            break;
                    }
                } 
            }

            return is_validation_ok;
        },

        
    }))



    

    models.load_models({
        // model: 'pos.order.note',
        model: 'res.partner.category',
        fields: ['name'],
        loaded: function (self, ordernotes) {
            self.order_note_by_id = {};
            for (var i = 0; i < ordernotes.length; i++) {
                self.order_note_by_id[ordernotes[i].id] = ordernotes[i];
            }
        },
    });
    

    var NotePopupWidget = PopupWidget.extend({
        count: 0,
        template: 'NotePopupWidget',
        events: _.extend({}, PopupWidget.prototype.events, {
            'change .note_temp': 'click_option',
            'click .remove': 'click_remove',
        }),
        init: function (parent, options) {
            this.options = options || {};
            this._super(parent, _.extend({}, {
                size: "medium"
            }, this.options));
        },
        renderElement: function () {
            this._super();
            for (var note in this.pos.order_note_by_id) {
                $('#note_select').append($("<option>" + this.pos.order_note_by_id[note].name + "</option>").attr("value", this.pos.order_note_by_id[note].name)
                    .attr("id", this.pos.order_note_by_id[note].id)
                    .attr("class", "note_option"))
            }
        },
        show: function (options) {
            options = options || {};
            this._super(options);
            $('textarea').text(options.value);
        },
        click_confirm: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var line = this.pos.get_order().get_selected_orderline();
            line.set_note($('#note_text_area').val());
            this.gui.close_popup();
        },
        click_remove: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var old_text = $('textarea').val();
            console.log("From Remove Option")
            console.log(old_text)
            var all_text = old_text.split(", ");
            var text = "";
            for(var i=0;i<all_text.length-1;i++)
            {
                if (i>0)
                {
                    text += ", "
                }
                text += all_text[i]
            }
            console.log(text)
            $('textarea').text(text);
        },
        click_option: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var old_text = $('textarea').val();
            var e = document.getElementById("note_select");
            var text = e.options[e.selectedIndex].value;
            console.log(old_text);
            console.log(text);
            if (old_text.length > 0)
            {
                old_text += ", ";
            }
            // old_text += "\n";
            old_text += text;
            console.log(old_text)
            $('textarea').text(old_text);
        }

    });
    gui.define_popup({name: 'pos_no', widget: NotePopupWidget});

    var ChronicDisease = screens.ActionButtonWidget.extend({
        template: 'ChronicDisease',
        button_click: function () {
            var line = this.pos.get_order().get_selected_orderline();
            if (line) {
                this.gui.show_popup('pos_no', {
                    value: line.get_note(),
                    'title': _t('Select Chronic Disease')
                });
            }
        }
    });

    screens.define_action_button({
        'name': 'pos_internal_note',
        'widget': ChronicDisease,
        'condition': function () {
            return this.pos.config.note_config;
        }
    });


    

    screens.ClientListScreenWidget.include(({
        dependent_information: function(partner_id){
            var partner = this.pos.db.get_partner_by_id(partner_id);
            return partner;
        }
    }));
});

