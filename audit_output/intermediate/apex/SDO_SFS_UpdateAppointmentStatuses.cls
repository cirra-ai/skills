public with sharing class SDO_SFS_UpdateAppointmentStatuses {

    public class InputWrapper {
        @InvocableVariable(label='Service Territory Id' required=true)
        public Id serviceTerritoryId;

        @InvocableVariable(label='Start Date' required=true)
        public Date startDate;

        @InvocableVariable(label='End Date' required=true)
        public Date endDate;
    }

    @InvocableMethod(label='Randomize Appointment Statuses by Service Territory')
    public static void updateStatuses(List<InputWrapper> inputList) {
        if (inputList == null || inputList.isEmpty()) return;

        InputWrapper input = inputList[0];
        if (input.serviceTerritoryId == null || input.startDate == null || input.endDate == null) {
            throw new AuraHandledException('Missing input values.');
        }

        // 🔄 Step 1: Get ServiceResourceIds from ServiceTerritory
        List<Id> serviceResourceIds = new List<Id>();
        for (ServiceTerritoryMember stm : [
            SELECT ServiceResourceId
            FROM ServiceTerritoryMember
            WHERE ServiceTerritoryId = :input.serviceTerritoryId
        ]) {
            serviceResourceIds.add(stm.ServiceResourceId);
        }

        if (serviceResourceIds.isEmpty()) return;

        Integer dayCount = input.startDate.daysBetween(input.endDate);
        List<ServiceAppointment> updates = new List<ServiceAppointment>();

        for (Id resourceId : serviceResourceIds) {
            for (Integer d = 0; d <= dayCount; d++) {
                Date currentDate = input.startDate.addDays(d);
                DateTime dayStart = DateTime.newInstance(currentDate, Time.newInstance(0, 0, 0, 0));
                DateTime dayEnd = dayStart.addDays(1);

                List<AssignedResource> arList = [
                    SELECT ServiceAppointment.Id,
                           ServiceAppointment.Status,
                           ServiceAppointment.SchedStartTime
                    FROM AssignedResource
                    WHERE ServiceResourceId = :resourceId
                    AND ServiceAppointment.SchedStartTime >= :dayStart
                    AND ServiceAppointment.SchedStartTime < :dayEnd
                    AND ServiceAppointmentId != NULL
                    ORDER BY ServiceAppointment.SchedStartTime ASC
                    LIMIT 8
                ];

                List<ServiceAppointment> dailyAppointments = new List<ServiceAppointment>();
                for (AssignedResource ar : arList) {
                    if (ar.ServiceAppointment != null) {
                        dailyAppointments.add(ar.ServiceAppointment);
                    }
                }

                Integer count = dailyAppointments.size();
                if (count == 0) continue;

                Integer backCount = (count >= 6) ? 2 : 1;

                // Assign last 1–2 to Scheduled/Dispatched/In Progress
                for (Integer i = count - backCount; i < count; i++) {
                    dailyAppointments[i].Status = getRandomFrom(new List<String>{'Scheduled', 'Dispatched', 'In Progress'});
                }

                // Assign others: Mostly Completed + 1 Canceled/Cannot Complete
                List<String> statusPool = new List<String>();
                Integer completedCount = count - backCount - 1;

                for (Integer i = 0; i < completedCount; i++) {
                    statusPool.add('Completed');
                }
                statusPool.add(getRandomFrom(new List<String>{'Canceled', 'Cannot Complete'}));

                statusPool = shuffleStrings(statusPool);
                for (Integer i = 0; i < count - backCount; i++) {
                    dailyAppointments[i].Status = statusPool[i];
                }

                updates.addAll(dailyAppointments);
            }
        }

        if (!updates.isEmpty()) {
            update updates;
        }
    }

    private static String getRandomFrom(List<String> options) {
        Integer index = Math.mod(Math.abs(Crypto.getRandomInteger()), options.size());
        return options[index];
    }

    private static List<String> shuffleStrings(List<String> input) {
        List<String> result = new List<String>(input);
        for (Integer i = result.size() - 1; i > 0; i--) {
            Integer j = Math.mod(Math.abs(Crypto.getRandomInteger()), i + 1);
            String temp = result[i];
            result[i] = result[j];
            result[j] = temp;
        }
        return result;
    }
}