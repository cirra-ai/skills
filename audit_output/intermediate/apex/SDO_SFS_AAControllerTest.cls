@isTest
public with sharing class SDO_SFS_AAControllerTest {
    @isTest
    static void testGetAssetId() {
        // Create test data
        account tAccount = new account();
        tAccount.name = 'testAccount';
        database.insert( tAccount);
        asset tAsset = new asset();
        tAsset.AccountId = tAccount.id;
        tAsset.Name = 'testAsset';
        database.insert( tAsset);
        workorder tWO = new workorder();
        tWO.Subject = 'testWO';
        tWO.AccountId = tAccount.id;
        tWO.AssetId = tAsset.Id;
        database.insert( tWO);

        String assetId = SDO_SFS_AAController.getAssetId(tWO.Id);

        System.assert(assetId<>null);
    }

    @isTest(SeeAllData=true)
    static void testGetAssetAttributes() {

        asset tAsset = [select id,name,accountid from asset where id in 
        (select assetid from assetattribute where attributepicklistvalueid = null) 
         limit 1 ];
        workorder tWO = new workorder();
        tWO.Subject = 'testWO1';
        tWO.AccountId = tAsset.AccountId;
        tWO.AssetId = tAsset.Id;
        database.insert( tWO);

        assetattribute aa1 = [select id, attributevalue from assetattribute where assetid =: tasset.id and attributepicklistvalueid = null limit 1];
        aa1.AttributeValue = '3';
        database.updateimmediate( aa1);

        attributepicklistvalue aplv = [select id from attributepicklistvalue limit 1];
        assetattribute aa2 = [select id, attributevalue from assetattribute where assetid =: tasset.id and attributepicklistvalueid != null limit 1];
        aa2.AttributeValue = aplv.id;
        database.updateimmediate( aa2);

        List<SDO_SFS_AAController.AAwithPicklistValues> assetAttributes = SDO_SFS_AAController.getAssetAttributes(tAsset.id, tWO.id);
        System.assert(assetAttributes.size()>0);
       
        SDO_SFS_AAController.saveAttribute(aa1.id, '3'); 

    }
}