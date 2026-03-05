//Test for BoostBuryController 
@isTest
public with sharing class sdo_scom_boost_and_bury_controller_test {
    static testMethod void testCallout() {
        sdo_scom_boost_and_bury_controller_mock.statusCode = 200;
        Test.setMock(HttpCalloutMock.class, new sdo_scom_boost_and_bury_controller_mock());  
        //success test case
        Assert.areEqual('{}', sdo_scom_boost_and_bury_controller.callOut('TEST URL', 'POST', null, '{}'), 'call out is working fine');
        Assert.areEqual('{}', sdo_scom_boost_and_bury_controller.getRule(''), 'call out is working fine');
        Assert.areEqual('{}', sdo_scom_boost_and_bury_controller.createRule('', ''), 'call out is working fine');
        Assert.areEqual('{}', sdo_scom_boost_and_bury_controller.deleteRule('', ''), 'call out is working fine');


        sdo_scom_boost_and_bury_controller_mock.statusCode = 500;
        sdo_scom_boost_and_bury_controller_mock.requestBody = '[{"message" : "Test"}]';

        try{
            //failure test case
            sdo_scom_boost_and_bury_controller.callOut('TEST URL', 'POST', null, '');
            Assert.areEqual('Test', '', 'call out is not working fine');
        }catch(Exception exc){
            Assert.areEqual('Test', exc.getMessage().trim(), 'call out is not working fine');
        }
    }

    static testMethod void validateProducts() {
        Product2 productRecord = new Product2(Name = 'Test', isActive = true);
        insert productRecord;
        Assert.areEqual(1, sdo_scom_boost_and_bury_controller.getProducts().size(), 'Number of product is 1');
        Assert.areEqual(1, sdo_scom_boost_and_bury_controller.getProductsById(new List<String>{productRecord.Id}).size(), 'Number of product is 1');
    }
}