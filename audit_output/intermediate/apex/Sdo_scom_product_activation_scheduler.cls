public with sharing class Sdo_scom_product_activation_scheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        Sdo_scom_product_activation_service service = new Sdo_scom_product_activation_service();
        service.checkAndUpdateProductStatus();
    }
}