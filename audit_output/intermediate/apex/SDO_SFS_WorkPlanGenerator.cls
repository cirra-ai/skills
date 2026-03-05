public with sharing class SDO_SFS_WorkPlanGenerator {

    @AuraEnabled
    public static String generateWorkPlans(WorkOrder woInput) {
        try {
            WorkOrder wo=[SELECT Id,WorkType.Name from WorkOrder where Id=:woInput.Id LIMIT 1];
            // Create Work Plan Template
            String planName = (wo?.WorkType?.Name ?? '') + ' Work Plan';
            WorkPlan workPlan = new WorkPlan(
                Name = planName,
                ParentRecordId=wo.Id
            );

            insert workPlan;

            // Safely re-query to get the actual Id
            

            // Create Work Steps
            List<WorkStep> workSteps = new List<WorkStep>{
                createWorkStep('Check In', 'Technician arrival and initial check-in process', 1, workPlan.Id, ''),
                createWorkStep('Review Pre-work Brief', 'Review work order details and safety requirements', 2, workPlan.Id, ''),
                createWorkStep('Review Asset Details', 'Inspect current battery system and verify replacement needs', 3, workPlan.Id, ''),
                createWorkStep('Troubleshooting (work type name )', 'Remove old battery and install new one if replacement is required', 4, workPlan.Id, ''),
                createWorkStep('Complete Work', 'Perform final checks and system testing', 5, workPlan.Id, ''),
                createWorkStep('Create Post Work Summary', 'Document work performed and any recommendations', 6, workPlan.Id, ''),
                createWorkStep('Check Out', 'Complete final documentation and site cleanup', 7, workPlan.Id, '')
            };

            try {
                // upsert workSteps External_ID__c;
                insert workSteps;
            } catch (DmlException dmlEx) {
                for (Integer i = 0; i < dmlEx.getNumDml(); i++) {
                    System.debug('DML Error: ' + dmlEx.getDmlMessage(i));
                }
                throw new AuraHandledException('Failed to upsert work steps: ' + dmlEx.getMessage());
            }

            return 'Successfully created Battery Replacement Work Plan template with ' + workSteps.size() + ' steps';
        } catch (Exception e) {
            System.debug('Error in generateWorkPlans: ' + e.getMessage());
            throw new AuraHandledException('Failed to create work plan: ' + e.getMessage());
        }
    }

    private static WorkStep createWorkStep(String name, String description, Integer order, Id workPlanId, String actionDefinition) {
        return new WorkStep(
            Name = name,
            Description = description,
            ExecutionOrder = order,
            WorkPlanId = workPlanId,
            Status = 'New',
            ActionDefinition = actionDefinition
        );
    }
}