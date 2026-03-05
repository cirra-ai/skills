public with sharing class SDO_SFS_WorkOrderTriggerHandler {

    public static void handleAfterInsert(List<WorkOrder> newWorkOrders) {
        if (newWorkOrders == null || newWorkOrders.isEmpty()) {
            return;
        }

        try {
            // Check if Work Plan exists
            
            	for(WorkOrder wo:newWorkOrders)
                SDO_SFS_WorkPlanGenerator.generateWorkPlans(wo);
            
        } catch (Exception e) {
            System.debug('Error in WorkOrderAfterInsert handler: ' + e.getMessage());
        }
    }
}