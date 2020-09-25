odoo.define('custom-button.custom_button', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');

    // Start Custom Code
    var OTP = screens.ActionButtonWidget.extend({
        template: 'OTP',
        button_click: function(){
            
            var self = this;
            this._super();

            var cust_phone = '+8801738169709';
            var settings = {
                "async": false,
                "crossDomain": true,
                "url": "https://cors-anywhere.herokuapp.com/https://mjn32.api.infobip.com/2fa/1/pin",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": "Basic RnV0dXJlVGVjaEJEMjpGdXR1cmVUZWNoQEJEITIwMTc="
                },
                "processData": false,
                "data": '{ \n\"applicationId\": \"4C7FC375AA0C53DC008998A05B8D5A8F\", \n\"messageId\": \"F0AF3A0D0B3292C2161E389AA472ED90\", \n\"from\": \"8804445667766\", \n\"to\": \"'+ cust_phone +'\" \n}'    
            }

            var pinId;
            // $.ajax(settings).done(function (response) {
            //     pinId = response.pinId;
            //     console.log(pinId);
            // });
     
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'pos.popup',        
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });

        },
    });
    
    screens.define_action_button({
        'name': 'OTP',
        'widget': OTP,
    });
    // End Custom Code
    
});