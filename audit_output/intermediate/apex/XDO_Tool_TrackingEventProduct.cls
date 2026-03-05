/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */


/**
     @author        Paul Lucas
     @company       Salesforce
     @description   
     @date          11/1/2024

     TODO:
 */

public without sharing virtual class XDO_Tool_TrackingEventProduct extends XDO_Tool_TrackingEvent //NOPMD
{
    public final String ERROR_CODE_DEFAULT = '400';

    public enum TRACKING_EVENT {
        Api_Called, Element_Clicked, Element_Hovered, Error, Exception_x, Page_Viewed
    }

    public enum TRACKING_PROPERTY {
        code,
        message
    }

    public XDO_Tool_TrackingEventProduct() {
//        super(TRACKING_EVENT_TYPE.Product);
    }

    public XDO_Tool_TrackingEventProduct(TRACKING_EVENT event) {
        super(TRACKING_EVENT_TYPE.Product, event.name());
    }

    @InvocableMethod(Label='Capture Product Development Tracking Event' Description='Capture a product development tracking event' Category='XDO Tool - Tracking Event' IconName='slds:utility:send_log')
    public static void publish(List<XDO_Tool_TrackingEvent> trackingEvents) {
        System.debug('>>>>> SDO_Tool_TrackingEventProduct.publish: ');
        System.debug(trackingEvents);

        for (XDO_Tool_TrackingEvent event : trackingEvents) {
            event.setType(TRACKING_EVENT_TYPE.Product)
                    .publish();
        }
    }

    public class Error extends XDO_Tool_TrackingEventProduct {
        public Error() {
            super(TRACKING_EVENT.Error);
            setCode(ERROR_CODE_DEFAULT);
        }

        public Error(String message) {
            this();
            setMessage(message);
        }

        public Error setCode(String value) {
            this.addProperty(TRACKING_PROPERTY.code.name(), value);

            return this;
        }

        public Error setMessage(String value) {
            this.addProperty(TRACKING_PROPERTY.message.name(), value);

            return this;
        }
    }
}