/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */

@IsTest
public with sharing class B2BCrossSellTestUtils {

    public static User createAdminUser() {

        System.debug('inside createAdminUser()');

        User u = new User();

        u.Username = 'testb2buser1@test.com';
        u.LastName = 'TestLastName';
        u.Email = 'testb2buser1@test.com';
        u.Alias = 'test1';
        u.TimeZoneSidKey = 'America/New_York';
        u.EmailEncodingKey = 'ISO-8859-1';
        u.ProfileId = [select id from Profile where Name = 'System Administrator'].Id;
        u.LanguageLocaleKey = 'en_US';
        u.LocaleSidKey = 'en_US';
        u.EmployeeNumber = '655321';

        // Do not assign a role to the user.  If you do, this can cause issues with the scratch org you are creating the package in.

        insert u;

        return u;
    }

    public static Id createUser(Id contactId) {

        System.debug('inside createUser()');

        User u = new User();

        u.Username = 'testb2buser2@test.com';
        u.LastName = 'TestLastName';
        u.Email = 'testb2buser2@test.com';
        u.Alias = 'test2';
        u.TimeZoneSidKey = 'America/New_York';
        u.EmailEncodingKey = 'ISO-8859-1';

        u.ProfileId = [select id from Profile where Name = 'Standard User'].Id;
        
        u.LanguageLocaleKey = 'en_US';
        u.LocaleSidKey = 'en_US';
        u.EmployeeNumber = '24601';
        u.ContactId = contactId;

        // Do not assign a role to the user.  If you do, this can cause issues with the scratch org you are creating the package in.

        insert u;

        return u.Id;
    }

    public static void assignPermissionSetToUser(Id userId, String permissionSetName) {

        System.debug('inside assignPermissionSetToUser()');

        PermissionSet perm = [Select Id, Name from PermissionSet where Name = :permissionSetName];

        PermissionSetAssignment psa = new PermissionSetAssignment (
            PermissionSetId = perm.Id, AssigneeId = userId
        );

        insert psa;
    }
    
    public static Id createProduct(String name, String sku, String description) {
        Product2 product = new Product2(
            IsActive = true
            , Name = name
            , StockKeepingUnit = sku
            , Description = description
        );

        insert product;

        return product.Id;

    }

    public static Id createCrossSellItem(Id parentProductId, Id crossProductId) {

        Cross_Sell_Recommendations__c cross = new Cross_Sell_Recommendations__c(
            Recommended_Product_Parent__c = parentProductId
            , Recommended_Product__c = crossProductId
        );

        insert cross;

        return cross.Id;

    }

    public static Id createCrossSellItem(Id parentProductId, Id crossProductId, String productType) {

        Cross_Sell_Recommendations__c cross = new Cross_Sell_Recommendations__c(
            Recommended_Product_Parent__c = parentProductId
            , Recommended_Product__c = crossProductId
            , Product_Type__c = productType
        );

        insert cross;

        return cross.Id;

    }

    public static Cross_Sell_Recommendations__c getCrossSellItem(Id bundleItemId) {

        List<Cross_Sell_Recommendations__c> crossList = [Select Id, Name, Product_Type__c, Recommended_Product__c, Recommended_Product_Parent__c from Cross_Sell_Recommendations__c where Id = :bundleItemId];

        Cross_Sell_Recommendations__c cross = null;

        if(crossList.size() > 0) {
            cross = crossList.get(0);
        }

        return cross;

    }

    public static Id createPricebook() {

        Pricebook2 pb = new Pricebook2(
            IsActive = true
            , Description = 'Default price book'
            , Name = 'Standard Price Book ' + getGuid()
        );

        insert pb;

        return pb.Id;
    }

    public static Id createStandardPricebookEntry(Id productId) {

        Id pricebookId = Test.getStandardPricebookId();

        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 2.98
            , Pricebook2Id = pricebookId
            , Product2Id = productId
        );

        insert pbe;

        return pbe.Id;
    }

    public static Id createPricebookEntry(Id pricebookId, Id productId) {
        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 1.98
            , Pricebook2Id = pricebookId
            , Product2Id = productId
        );

        insert pbe;

        return pbe.Id;
    }

    public static String getGuid() {
        Blob b = Crypto.generateAesKey(128);
        String h = EncodingUtil.convertToHex(b);
        String guid = h.substring(0,8) + '-' + h.substring(8,12) + h.substring(12,16) + '-' + h.substring(16,20) + '-' + h.substring(20);

        return guid;
    }

    public static Product2 getProduct(String productId) {
        List<Product2> productList = [Select Id, Name, StockKeepingUnit from Product2 where Id = :productId];

        Product2 product = null;

        if(productList.size() > 0) {
            product = productList.get(0);
        }

        return product;
    }

    public static PricebookEntry getPricebookEntry(String pbeId, String productId) {

        List<PricebookEntry> pbeList = [Select Id, UnitPrice from PricebookEntry where Id = :pbeId and Product2Id = :productId];

        PricebookEntry pbe = null;
        if(pbeList.size() > 0) {
            pbe = pbeList.get(0);
        }

        return pbe;

    }

    public static Id createAccount() {

        System.debug('inside createAccount()');

        Account account = new Account();

        account.Name = 'Ohana, LLC';
        account.Type = 'Customer';
        account.Phone = '1-313-555-1212';
        account.Website = 'https://detroit.org';

        insert account;

        return account.Id;
    }

    // For the ConnectApi test coverage

    public static ConnectApi.ProductDetail getProductDetail(Id productId) {

        ConnectApi.ProductDetail pd = new ConnectApi.ProductDetail();

        Product2 product = [Select Id, Name, Description, StockKeepingUnit from Product2 where Id = :productId];

        pd.id = product.Id;
        
        Map<String, String> fieldMap = new Map<String, String>();
        fieldMap.put('StockKeepingUnit', product.StockKeepingUnit);
        fieldMap.put('Name', product.Name);
        fieldMap.put('Description', product.Description);

        pd.fields = fieldMap;

        return pd;

    }

    public static ConnectApi.ProductPrice getProductPrice(Id productId) {

        ConnectApi.ProductPrice price = new ConnectApi.ProductPrice();

        Id stdPricebookId = Test.getStandardPricebookId();

        List<PricebookEntry> pbeList = [Select Id, Name, Pricebook2Id, Pricebook2.IsStandard, UnitPrice from PricebookEntry where Product2Id = :productId];

        System.debug('pbeList.size() = ' + pbeList.size());

        System.debug(JSON.serialize(pbeList));

        if(pbeList.size() > 0) {
            for(PricebookEntry pbe : pbeList) {

                if(pbe.Pricebook2Id == stdPricebookId) {
                    System.debug('standard price found');
                    price.listPrice = pbe.UnitPrice.format();
                }
                else {
                    price.unitPrice = pbe.UnitPrice.format();
                }

            }
        }

        return price;
    }

}