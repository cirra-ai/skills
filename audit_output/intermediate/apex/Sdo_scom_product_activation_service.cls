public with sharing class Sdo_scom_product_activation_service {
    public void checkAndUpdateProductStatus() {
        List<Product2> productsToUpdate = new List<Product2>();        
        List<Product2> products = [SELECT Id, Start_Date_Time__c, End_Date_Time__c, IsActive 
                                   FROM Product2 
                                   WHERE Start_Date_Time__c != null AND End_Date_Time__c != null];
        
        // System.debug('products: ' + products);
        DateTime currentDateTime = DateTime.now();
        
        for (Product2 product : products) {
            if (currentDateTime >= product.Start_Date_Time__c && currentDateTime <= product.End_Date_Time__c) {
                if (!product.IsActive) {
                    product.IsActive = true;
                    productsToUpdate.add(product);
                }
            } else {
                if (product.IsActive) {
                    product.IsActive = false;
                    productsToUpdate.add(product);
                }
            }
        }
        
        if (!productsToUpdate.isEmpty()) {
            update productsToUpdate;
        }
    }
}