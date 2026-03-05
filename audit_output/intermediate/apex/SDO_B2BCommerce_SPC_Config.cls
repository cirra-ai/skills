public with sharing class SDO_B2BCommerce_SPC_Config {

    public static void updateAndDeployMetadata() {

        createDeliveryMethods();
    
        createTaxRates();
      }

      public static void createDeliveryMethods() {

        Metadata.DeployContainer mdContainer = new Metadata.DeployContainer();

        DeliveryMethodMeta del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.FedEx_Standard_Overnight', 'FedEx Standard Overnight', true, 'Overnight Delivery', 'FedEx', 'FEDEXSTDOVR', 20, 0);
        Metadata.CustomMetadata customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.FedEx_2_Day', 'FedEx 2 Day', true, '2 Day Delivery', 'FedEx', 'FEDEX2D', 10, 0);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.DHL_Free_Shipping', 'DHL Free Shipping', true, 'Free shipping', 'DHL', 'DHLFREE', 0, 0);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.DHL_Next_day', 'DHL Next day', true, 'Next day', 'DHL', 'DHLND', 9.99, 1.99);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.DHL_Next_Day_9am', 'DHL Next Day 9am', true, 'Next Day 9am', 'DHL', 'DHLND9', 39.99, 2.99);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.No_Shipping', 'No Shipping', false, 'No Shipping Charge', 'None', 'FREE', 0, 0);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.UPS_4_hours', 'UPS 4 hours', true, '4 hours', 'UPS', 'UPDS4H', 16.99, 1.99);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.UPS_Next_Day', 'UPS Next Day', true, 'Next day', 'UPS', 'UPDSND', 8.99, 1.99);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        del = new DeliveryMethodMeta('B2B_SPC_Delivery_Method.UPS_Standard_3_6_days', 'UPS Standard 3-6 days', true, 'Standard 3-6 days', 'UPS', 'UPDSTD', 0, 0);
        customMetadata = createDeliveryMethodMetadata(del);
        mdContainer.addMetadata(customMetadata);

        // Setup deploy callback, MyDeployCallback implements
        // the Metadata.DeployCallback interface (code for
        // this class not shown in this example)
        SDO_B2BCommerce_SPC_MyDeployCallback callback = new SDO_B2BCommerce_SPC_MyDeployCallback();
    
        // Enqueue custom metadata deployment
        Id deployRequestId = Metadata.Operations.enqueueDeployment(mdContainer, callback);

      }

      public static Metadata.CustomMetadata createDeliveryMethodMetadata(DeliveryMethodMeta del) {

        Metadata.CustomMetadata customMetadata =  new Metadata.CustomMetadata();
        customMetadata.fullName = del.fullName;
          
        customMetadata.label = del.label;

        Map<String, Object> customMetaMap = del.customMetaMap;
    
        for(String key : customMetaMap.keySet()) {
            String fieldName = key;
            Object fieldValue = customMetaMap.get(key);

            Metadata.CustomMetadataValue customField = new Metadata.CustomMetadataValue();

            customField.field = fieldName;
            customField.value = fieldValue;

            customMetadata.values.add(customField);
        }

        return customMetadata;

      }

      class DeliveryMethodMeta {

        public String fullname;
        public String label;

        public Map<String, Object> customMetaMap;

        public DeliveryMethodMeta() {
            customMetaMap = new Map<String, Object>();
        }

        public DeliveryMethodMeta(String fullName, String label, Boolean activeValue, String descriptionValue, String providerNameValue, String serviceCodeValue, Decimal shipmentCostValue, Decimal otherCostValue) {
            this();

            this.fullname = fullname;
            this.label = label;

            addActiveField(activeValue);
            addDescriptionField(descriptionValue);
            addOtherCostField(otherCostValue);
            addProviderNameField(providerNameValue);
            addServiceCodeField(serviceCodeValue);
            addShipmentCostField(shipmentCostValue);

        }


        public void addActiveField(Object fieldValue) {
            populateMap('Active__c', fieldValue);
          }
    
          public void addDescriptionField(Object fieldValue) {
            populateMap('Description__c', fieldValue);
          }
    
          public void addOtherCostField(Object fieldValue) {
            populateMap('Other_Cost__c', fieldValue);
          }
    
          public void addProviderNameField(Object fieldValue) {
            populateMap('Provider_Name__c', fieldValue);
          }
    
          public void addServiceCodeField(Object fieldValue) {
            populateMap('Service_Code__c', fieldValue);
          }
    
          public void addShipmentCostField(Object fieldValue) {
            populateMap('Shipment_Cost__c', fieldValue);
          }
    
          public void populateMap(String fieldName, Object fieldValue) {
            customMetaMap.put(fieldName, fieldValue);
          }

      }

      public static void createTaxRates() {

        Metadata.DeployContainer mdContainer = new Metadata.DeployContainer();

        TaxRateMeta tax = new TaxRateMeta('B2B_SPC_Tax_Rates.California', 'California', true, 'USA', .07, 'CA');
        Metadata.CustomMetadata customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.Colorado', 'Colorado', true, 'USA', .08, 'CO');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.Default', 'Default', true, '*', .08, '*');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.Georgia', 'Georgia', true, 'USA', .04, 'GA');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.Illinois', 'Illinois', true, 'USA', .06, 'IL');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.Michigan', 'Michigan', true, 'USA', .06, 'MI');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);

        tax = new TaxRateMeta('B2B_SPC_Tax_Rates.No_Tax', 'No Tax', false, '*', 0, '*');
        customMetadata = createTaxRateMetadata(tax);
        mdContainer.addMetadata(customMetadata);
        

        // Setup deploy callback, MyDeployCallback implements
        // the Metadata.DeployCallback interface (code for
        // this class not shown in this example)
        SDO_B2BCommerce_SPC_MyDeployCallback callback = new SDO_B2BCommerce_SPC_MyDeployCallback();
    
        // Enqueue custom metadata deployment
        Id deployRequestId = Metadata.Operations.enqueueDeployment(mdContainer, callback);

      }

      public static Metadata.CustomMetadata createTaxRateMetadata(TaxRateMeta tax) {

        Metadata.CustomMetadata customMetadata =  new Metadata.CustomMetadata();
        customMetadata.fullName = tax.fullName;
          
        customMetadata.label = tax.label;

        Map<String, Object> customMetaMap = tax.customMetaMap;
    
        for(String key : customMetaMap.keySet()) {
            String fieldName = key;
            Object fieldValue = customMetaMap.get(key);

            Metadata.CustomMetadataValue customField = new Metadata.CustomMetadataValue();

            customField.field = fieldName;
            customField.value = fieldValue;

            customMetadata.values.add(customField);
        }

        return customMetadata;

      }

      class TaxRateMeta {

        public String fullname;
        public String label;

        public Map<String, Object> customMetaMap;

        public TaxRateMeta() {
            customMetaMap = new Map<String, Object>();
        }

        public TaxRateMeta(String fullName, String label, Boolean activeValue, String countryValue, Decimal rateValue, String stateProvinceValue) {
            this();

            this.fullname = fullname;
            this.label = label;

            addActiveField(activeValue);
            addCountryField(countryValue);
            addRateField(rateValue);
            addStateProvinceField(stateProvinceValue);

        }

        public void addActiveField(Object fieldValue) {
            populateMap('Active__c', fieldValue);
          }
    
          public void addCountryField(Object fieldValue) {
            populateMap('Country__c', fieldValue);
          }
    
          public void addRateField(Object fieldValue) {
            populateMap('Rate__c', fieldValue);
          }
    
          public void addStateProvinceField(Object fieldValue) {
            populateMap('State_Province__c', fieldValue);
          }

          public void populateMap(String fieldName, Object fieldValue) {
            customMetaMap.put(fieldName, fieldValue);
          }

      }

}