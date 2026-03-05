public with sharing class SDO_SFS_MoveDates {

    // INPUT wrapper for Flow
    public class MoveRequest {
        @InvocableVariable(label='Start Date' required=true)
        public Date startDate;

        @InvocableVariable(label='End Date' required=true)
        public Date endDate;

        @InvocableVariable(
            label='Move Date'
            required=true
            description='Date to which SAs will be shifted'
        )
        public Date moveDate;
    }

    // OUTPUT wrapper for Flow
    public class MoveResult {
        @InvocableVariable(label='Appointments Moved')
        public Integer movedCount;
    }



    @InvocableMethod(label='Move Service Appointments')
    public static List<MoveResult> moveAppointments(List<MoveRequest> requests) {
        List<MoveResult> results = new List<MoveResult>();
        if (requests == null || requests.isEmpty()) {
             MoveResult res=new MoveResult();
            res.movedCount=0;
            results.add(res);
            return results;
        }
      
        MoveRequest req = requests[0];

        // 1) Compute days to shift
        Integer shiftDays = req.startDate.daysBetween(req.moveDate);

     TimeZone tz = UserInfo.getTimeZone();

// 2) build a GMT‐based DateTime at 00:00:00 and 23:59:59
DateTime startGMT = DateTime.newInstanceGmt(
    req.startDate.year(),
    req.startDate.month(),
    req.startDate.day(),
    0, 0, 0
);
DateTime endGMT = DateTime.newInstanceGmt(
    req.endDate.year(),
    req.endDate.month(),
    req.endDate.day(),
    23, 59, 59
);


        System.debug(startGMT);
                System.debug(endGMT);

        // 3) Query appointments in window
        List<ServiceAppointment> toUpdate = [
            SELECT Id,
                   ArrivalWindowStartTime,
                   ArrivalWindowEndTime,
                   SchedStartTime,
                   SchedEndTime,
                   EarliestStartTime,
                   DueDate
              FROM ServiceAppointment
             WHERE EarliestStartTime >= :startGMT
               AND EarliestStartTime < :endGMT
        ];

        // 4) Shift each non-null field and stamp Move_Date__c
        for (ServiceAppointment sa : toUpdate) {
            if (sa.ArrivalWindowStartTime != null) {
                sa.ArrivalWindowStartTime = sa.ArrivalWindowStartTime.addDays(shiftDays);
            }
            if (sa.ArrivalWindowEndTime != null) {
                sa.ArrivalWindowEndTime = sa.ArrivalWindowEndTime.addDays(shiftDays);
            }
            if (sa.SchedStartTime != null) {
                sa.SchedStartTime = sa.SchedStartTime.addDays(shiftDays);
            }
            if (sa.SchedEndTime != null) {
                sa.SchedEndTime = sa.SchedEndTime.addDays(shiftDays);
            }
            if (sa.EarliestStartTime != null) {
                sa.EarliestStartTime = sa.EarliestStartTime.addDays(shiftDays);
            }
            if (sa.DueDate != null) {
                sa.DueDate = sa.DueDate.addDays(shiftDays);
            }
        }

        // 5) Perform the update and capture the count
        Integer moved = 0;
        if (!toUpdate.isEmpty()) {
            update toUpdate;
            moved = toUpdate.size();
        }

        // 6) Return the result wrapper
        MoveResult res = new MoveResult();
        res.movedCount = moved;
        results.add(res);
        return results;
    }
}