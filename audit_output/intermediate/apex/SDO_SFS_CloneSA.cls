public with sharing class SDO_SFS_CloneSA {

    public class InputWrapper {
        @InvocableVariable(required=true label='Service Appointment Ids')
        public List<Id> serviceAppointmentIds;

        @InvocableVariable(required=true label='From Date')
        public Date fromDate;

        @InvocableVariable(required=true label='To Date')
        public Date toDate;

        @InvocableVariable(label='Schedule Appointments')
        public Boolean shouldSchedule;

        @InvocableVariable(label='Dispatch Appointments')
        public Boolean shouldDispatch;

        @InvocableVariable(label='Scheduling Policy Id')
        public Id schedulingPolicyId;
    }

    public class OutputWrapper {
        @InvocableVariable(label='Cloned Service Appointment Ids')
        public List<Id> clonedServiceAppointmentIds;
    }

    @InvocableMethod(label='Clone, Schedule, and Dispatch Service Appointments')
    public static List<OutputWrapper> cloneAppointments(List<InputWrapper> inputs) {
        List<OutputWrapper> results = new List<OutputWrapper>();
        if (inputs == null || inputs.isEmpty()) return results;

        InputWrapper input = inputs[0];

        if (input.serviceAppointmentIds == null || input.serviceAppointmentIds.isEmpty() ||
            input.fromDate == null || input.toDate == null || input.fromDate > input.toDate) {
            throw new AuraHandledException('Invalid inputs: Check ServiceAppointmentIds, FromDate, and ToDate.');
        }

        List<ServiceAppointment> originalSAs = [
            SELECT Id, ParentRecordId, EarliestStartTime, DueDate, Subject, ServiceTerritoryId
            FROM ServiceAppointment
            WHERE Id IN :input.serviceAppointmentIds
        ];

        List<ServiceAppointment> clonedSAs = new List<ServiceAppointment>();
        List<Id> clonedSAIds = new List<Id>();
        Integer numDays = input.fromDate.daysBetween(input.toDate);

        for (Integer i = 0; i <= numDays; i++) {
            Date currentDate = input.fromDate.addDays(i);
            Date dueDate = currentDate.addDays(3);

            for (ServiceAppointment sa : originalSAs) {
                ServiceAppointment newSA = sa.clone(false, true, false, false);
                newSA.EarliestStartTime = DateTime.newInstance(currentDate, Time.newInstance(9, 0, 0, 0));
                newSA.DueDate = DateTime.newInstance(dueDate, Time.newInstance(17, 0, 0, 0));
                newSA.Subject = sa.Subject + ' - Copy ' + currentDate.format();
                newSA.ParentRecordId = sa.ParentRecordId;
                newSA.ServiceTerritoryId = sa.ServiceTerritoryId;
                newSA.FSL__Auto_Schedule__c = input.shouldSchedule;
                clonedSAs.add(newSA);
            }
        }

        insert clonedSAs;

        for (ServiceAppointment sa : clonedSAs) {
            clonedSAIds.add(sa.Id);
        }

      
        

        OutputWrapper output = new OutputWrapper();
        output.clonedServiceAppointmentIds = clonedSAIds;
        results.add(output);
        return results;
    }


}