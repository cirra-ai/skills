public without sharing class SDO_SFS_InventoryCountController {
    @AuraEnabled
    public static List<InventoryCountWrapper> getInventoryCountsForDate(Datetime inputDate) {
        // Query Inventory Count records where inputDate is between Planned Start and End Dates
        List<InventoryCountProductItem> counts = [
            SELECT 
                Id, 
                Name,
                Product,
                Actual_Quantity__c,
                PlannedStartDateTime,
                PlannedEndDateTime,
                ActualStartDateTime,
                ActualEndDateTime
            FROM InventoryCountProductItem
            WHERE PlannedStartDateTime <= :inputDate
            AND PlannedEndDateTime > :inputDate
        ];

        List<InventoryCountWrapper> wrappers = new List<InventoryCountWrapper>();
        for (InventoryCountProductItem ic : counts) {
            wrappers.add(new InventoryCountWrapper(
                ic.Id,
                ic.Name,
                ic.Product,
                ic.Actual_Quantity__c,
                ic.PlannedStartDateTime,
                ic.PlannedEndDateTime,
                ic.ActualStartDateTime,
                ic.ActualEndDateTime
            ));
        }

        return wrappers;
    }   

    @AuraEnabled
    public static void updateInventoryCounts(List<Map<String, Object>> updatedCounts) {
        List<InventoryCountProductItem> toUpdate = new List<InventoryCountProductItem>();
        
        for (Map<String, Object> countMap : updatedCounts) {
            String recordId = (String) countMap.get('recordId');
            Decimal quantity = (Decimal) countMap.get('quantity');
            
            if (String.isNotBlank(recordId)) {
                toUpdate.add(new InventoryCountProductItem(
                    Id = recordId,
                    Actual_Quantity__c  = quantity,
                    ActualStartDateTime = Datetime.now(),
                    ActualEndDateTime = Datetime.now()
                ));
            }
        }
        
        if (!toUpdate.isEmpty()) {
            try {
                update toUpdate;
            } catch (Exception e) {
                System.debug('Error updating InventoryCountProductItems: ' + e.getMessage());
                throw new AuraHandledException('Update failed: ' + e.getMessage() + ' -- ' + e.getStackTraceString());
            }
        }
    }

    // Wrapper class for use in LWC
    public class InventoryCountWrapper {
        @AuraEnabled public Id recordId;
        @AuraEnabled public String name;
        @AuraEnabled public String productName;
        @AuraEnabled public Decimal quantity;
        @AuraEnabled public Datetime plannedStartDate;
        @AuraEnabled public Datetime plannedEndDate;
        @AuraEnabled public Datetime actualStartDate;
        @AuraEnabled public Datetime actualEndDate;

        // No-arg constructor required for serialization/deserialization
        public InventoryCountWrapper() {}

        public InventoryCountWrapper(
            Id recordId, 
            String name, 
            String productName, 
            Decimal quantity, 
            Datetime plannedStartDate, 
            Datetime plannedEndDate,
            Datetime actualStartDate,
            Datetime actualEndDate
        ) {
            this.recordId = recordId;
            this.name = name;
            this.productName = productName;
            this.quantity = quantity;
            this.plannedStartDate = plannedStartDate;
            this.plannedEndDate = plannedEndDate;
            this.actualStartDate = actualStartDate;
            this.actualEndDate = actualEndDate;
        }
    }
}