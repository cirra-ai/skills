public class SDO_SFS_ASP {
    
    @AuraEnabled
    public static String createWorkPlan(Id woId,String workPlanName,String workStepName)
    {
        WorkPlan wp=new WorkPlan(Name=workPlanName,ParentRecordId =woId,ExecutionOrder =1);
        try
        {
            insert wp;
            WorkStep ws=new WorkStep(Name=workStepName,ExecutionOrder=1, WorkPlanId = wp.Id);
            insert ws;
        }
        catch(Exception ex)
        {
            return ex.getMessage();
        }
            
        return 'success';
    }
}