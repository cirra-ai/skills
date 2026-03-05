public without sharing class cxInCustomGuidanceCenterCls {
    @AuraEnabled
    public static List<CGC_Program__c> getActiveProgram(){
        List<CGC_Program__c> proplist = [ SELECT Id, Active__c, Due_Date__c, Description__c, Name, Completion_Percentage__c,Current_Value__c,Total_Milestones_and_Exercises__c,Milestone_Icon_Type__c
                                         FROM CGC_Program__c where Active__c = true];
        system.debug('program'+proplist);
        return proplist;   
    }
    @AuraEnabled
    public static SectionsListWrapper getSections(String progId) {
       
       
      List<CGC_Section__c> seclist = [
            SELECT Id, Name, Completion_Percentage__c,  Current_Value__c, Target_Value__c,Completed_Exercises__c, Completed_Milestones__c, Total_Milestones_and_Exercises__c,Completed__c,
            (SELECT Id, Name__c, Completed__c, Completion_Percentage__c, Due_Date__c, Current_Value__c,Description__c,Total_Target_Value__c,MilestoneIsTrue__c,Completed_Ex__c,Type__c,URL__c,Completed_On__c,Program_Outcome__c,Lesson_Description__c FROM Milestones_and_Exercises__r where Program_Outcome__c= False order by Due_Date__c ASC)
            FROM CGC_Section__c where Program__c=:progId
        ];
       
        List<CGC_Milestone_and_Exercise__c> progOutcomeList=[SELECT Id, Name__c, Completed__c, Completion_Percentage__c, Due_Date__c, Current_Value__c,Description__c,Total_Target_Value__c,MilestoneIsTrue__c,Completed_Ex__c,Type__c,URL__c,Completed_On__c,Program_Outcome__c,Lesson_Description__c FROM CGC_Milestone_and_Exercise__c where Program_Outcome__c= True AND Section__r.Program__c=:progId order by Due_Date__c ASC];  
        SectionsListWrapper secWrapper = new SectionsListWrapper();
        secWrapper.seclist=seclist;
       secWrapper.progOutcomeList=progOutcomeList;
        system.debug('Sections List'+seclist);
        system.debug('Sections'+secWrapper);
        return secWrapper;   
        
   
    }
      public class SectionsListWrapper{
        @AuraEnabled
        public List<CGC_Section__c> seclist{get;set;}
        @AuraEnabled
       public List<CGC_Milestone_and_Exercise__c> progOutcomeList {get;set;}
    }
    
    @AuraEnabled
    public static List<CGC_Program__c> getAllPrograms() {
        List<CGC_Program__c> allproglist =[SELECT Id, Active__c, Due_Date__c, Description__c, Name,Current_Value__c, Completion_Percentage__c FROM CGC_Program__c order by Due_Date__c ASC];
        system.debug('all programs'+allproglist);
        return allproglist;   
    }
    
    @AuraEnabled
    public static void activateProgram(string recordId){
        List<CGC_Program__c> allPrograms = [Select Id, Active__c from CGC_Program__c];
        for(CGC_Program__c program: allPrograms){
            if(program.Id == recordId){
                program.Active__c = true;
            }else{
                program.Active__c = false;
            }
        }
        update allPrograms;
    }
    
    @AuraEnabled
    public static void setExerciseAsComplete(string recordId){
        CGC_Milestone_and_Exercise__c exc = [Select Completed_Ex__c, Completed_On__c, Id from CGC_Milestone_and_Exercise__c  where Id =: recordId limit 1];
        exc.Completed_Ex__c = true;
        exc.Completed_On__c = date.today();
        update exc;
    }
    
    @AuraEnabled
    public static void resetProgress(string programId){
        List< CGC_Section__c > sc= [select id from CGC_Section__c where Program__c =: programId];
        List<CGC_Milestone_and_Exercise__c> m= [select id,Completed_Ex__c,Completed_On__c  from CGC_Milestone_and_Exercise__c where Section__c IN :sc];
        delete [select id from CGC_Milestone_Progress_V2__c where Milestone_and_Exercise__c IN :m];
        //  List<CGC_Milestone_and_Exercise__c> exrcs = [Select Completed_Ex__c, Completed_On__c, Id from CGC_Milestone_and_Exercise__c where Program__r.Id =: programId];
        for(CGC_Milestone_and_Exercise__c exc: m){
            exc.Completed_Ex__c  = false;
            exc.Completed_On__c = null;
        }
        update m;
    }
    
}