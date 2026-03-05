public class SDO_SFS_TimeSheetGenerator {

    // Inner class to define input parameters for the Invocable Method
    public class InputParameters {
        @InvocableVariable(required=true)
        public Date startDate;

        @InvocableVariable(required=true)
        public Date endDate;

        @InvocableVariable(required=true)
        public String serviceResourceExternalId;
    }

    // Inner class to define the result structure for the Invocable Method
    public class OutputResult {
        @InvocableVariable
        public Boolean isSuccess;
        @InvocableVariable
        public String message;
        @InvocableVariable
        public Id timeSheetId; // Optionally return the ID of the created TimeSheet
    }

    @InvocableMethod(label='Generate TimeSheets with Entries' description='Generates TimeSheet and TimeSheetEntry records for a given date range and Service Resource.')
    public static List<OutputResult> generateTimeSheets(List<InputParameters> inputs) {
        List<OutputResult> results = new List<OutputResult>();
        Set<Id> serviceResourceIds = new Set<Id>();
        Map<String, ServiceResource> srMap = new Map<String, ServiceResource>();

        // Collect all unique ServiceResource External IDs from inputs
        Set<String> uniqueSrExternalIds = new Set<String>();
        for (InputParameters input : inputs) {
            uniqueSrExternalIds.add(input.serviceResourceExternalId);
        }

        // Query all required ServiceResources in one go
        for (ServiceResource sr : [SELECT Id, External_ID__c FROM ServiceResource WHERE External_ID__c IN :uniqueSrExternalIds]) {
            srMap.put(sr.External_ID__c, sr);
        }

        for (InputParameters input : inputs) {
            OutputResult res = new OutputResult();
            res.isSuccess = false; // Assume failure until proven otherwise

            try {
                ServiceResource sr = srMap.get(input.serviceResourceExternalId);

                if (sr == null) {
                    res.message = 'ServiceResource with External_ID__c=\'' + input.serviceResourceExternalId + '\' not found.';
                    results.add(res);
                    continue; // Move to next input
                }

                // Define duration constraints
                Integer minWorkTimeDuration = 60; // minimum 1 hour work block
                Integer maxWorkTimeDuration = 100; // maximum 3 hours work block
                Integer minDriveTimeDuration = 5; // minimum drive time to ensure it's not 0
                Integer maxDriveTimeDuration = 30; // maximum 30 mins for drivetime
                Integer meetingDuration = Math.round(Math.random() * (60 - 30)) + 30; // Single meeting: 30 to 60 mins
                Integer breakDuration = 45; // Single break: exactly 45 mins

                List<TimeSheet> timeSheetsToInsert = new List<TimeSheet>();
                List<TimeSheetEntry> timeSheetEntriesToInsert = new List<TimeSheetEntry>();

                // Loop through the dates provided in the input range
                for (Date sheetDate = input.startDate; sheetDate <= input.endDate; sheetDate = sheetDate.addDays(1)) {
                    // --- Determine Flexible Day Start and End Times (9:00-9:30 AM to 5:30-6:00 PM) ---
                    Integer startBufferMinutes = Math.floor(Math.random() * 31).intValue(); // 0 to 30 minutes
                    Integer endBufferMinutes = Math.floor(Math.random() * 31).intValue();   // 0 to 30 minutes

                    Datetime actualDayStartTime = Datetime.newInstance(sheetDate.year(), sheetDate.month(), sheetDate.day(), 9, 0, 0).addMinutes(startBufferMinutes);
                    Datetime actualDayEndTime = Datetime.newInstance(sheetDate.year(), sheetDate.month(), sheetDate.day(), 18, 0, 0).addMinutes(-endBufferMinutes);

                    // Ensure actual day start is before actual day end, with at least a minimum working duration (e.g., 8 hours total)
                    Long totalDayDurationMillis = actualDayEndTime.getTime() - actualDayStartTime.getTime();
                    if (totalDayDurationMillis < (8 * 60 * 60 * 1000L)) { // If less than 8 hours, adjust end time
                        actualDayEndTime = actualDayStartTime.addHours(8);
                        // Ensure adjusted end time doesn't exceed 6 PM significantly
                        Datetime absoluteMaxEndTime = Datetime.newInstance(sheetDate.year(), sheetDate.month(), sheetDate.day(), 18, 0, 0);
                        if (actualDayEndTime > absoluteMaxEndTime) {
                            actualDayEndTime = absoluteMaxEndTime;
                        }
                    }
                    
                    // Create TimeSheet
                    TimeSheet ts = new TimeSheet(
                        ServiceResourceId = sr.Id,
                        StartDate = sheetDate,
                        EndDate = sheetDate,
                        StartDateTime = actualDayStartTime,  // Populate StartDateTime
                        EndDateTime = actualDayEndTime       // Populate EndDateTime
                    );
                    timeSheetsToInsert.add(ts);
                }

                // Insert TimeSheets to get their IDs
                if (!timeSheetsToInsert.isEmpty()) {
                    insert timeSheetsToInsert;
                }
                
                // Process entries for each inserted TimeSheet
                for (TimeSheet ts : timeSheetsToInsert) {
                    List<TimeSheetEntry> currentDayEntries = new List<TimeSheetEntry>();
                    Datetime currentProcessedTime = ts.StartDateTime; 

                    Boolean lastEntryWasWorkTime = false; 

                    // --- 1. First TimeSheetEntry: DriveTime (around 30 mins) ---
                    Integer firstDriveTimeDuration = (Integer)Math.floor(Math.random() * 11) + 25; // 25-35 mins
                    Datetime firstDriveEndTime = currentProcessedTime.addMinutes(firstDriveTimeDuration);

                    // Ensure it doesn't exceed the day's end time
                    if (firstDriveEndTime > ts.EndDateTime) {
                        firstDriveTimeDuration = (Integer) ((ts.EndDateTime.getTime() - currentProcessedTime.getTime()) / (1000 * 60));
                        firstDriveEndTime = ts.EndDateTime;
                    }

                    if (firstDriveTimeDuration > 0) {
                        currentDayEntries.add(new TimeSheetEntry(
                            TimeSheetId = ts.Id,
                            Status = 'New',
                            StartTime = currentProcessedTime,
                            EndTime = firstDriveEndTime,
                            Type = 'Direct',
                            Category = 'DriveTime'
                        ));
                        currentProcessedTime = firstDriveEndTime;
                    }


                    // --- 2. Schedule exactly one BreakTime (45 mins) between 1 PM and 2:30 PM ---
                    Datetime breakWindowStart = Datetime.newInstance(ts.StartDate.year(), ts.StartDate.month(), ts.StartDate.day(), 13, 0, 0); // 1 PM
                    Datetime breakWindowEnd = Datetime.newInstance(ts.StartDate.year(), ts.StartDate.month(), ts.StartDate.day(), 14, 30, 0);   // 2:30 PM

                    // Adjust break window to be within actual work hours and after currentProcessedTime
                    if (breakWindowStart < currentProcessedTime) breakWindowStart = currentProcessedTime; 
                    if (breakWindowEnd > ts.EndDateTime) breakWindowEnd = ts.EndDateTime; 

                    Integer availableBreakWindowMinutes = (Integer) ((breakWindowEnd.getTime() - breakWindowStart.getTime()) / (1000 * 60));

                    if (availableBreakWindowMinutes >= breakDuration) {
                        Integer randomOffsetWithinWindow = Math.floor(Math.random() * (availableBreakWindowMinutes - breakDuration + 1)).intValue();
                        Datetime breakStartTime = breakWindowStart.addMinutes(randomOffsetWithinWindow);
                        Datetime breakEndTime = breakStartTime.addMinutes(breakDuration);

                        // Final check if break fits cleanly
                        if (breakStartTime >= currentProcessedTime && breakEndTime <= ts.EndDateTime) {
                            currentDayEntries.add(new TimeSheetEntry(
                                TimeSheetId = ts.Id,
                                Status = 'New',
                                StartTime = breakStartTime,
                                EndTime = breakEndTime,
                                Type = 'Direct',
                                Category = 'BreakTime'
                            ));
                        } else {
                            System.debug('Warning: Could not schedule BreakTime cleanly for day: ' + ts.StartDate + '. Attempted Start: ' + breakStartTime + ', End: ' + breakEndTime);
                        }
                    } else {
                        System.debug('Warning: Not enough available time in break window for day: ' + ts.StartDate);
                    }

                    // --- 3. Schedule exactly one MeetingTime (30-60 mins) ---
                    Boolean meetingScheduled = false;

                    // Sort all pre-scheduled entries (initial DriveTime and BreakTime)
                    currentDayEntries.sort(); 

                    // --- 4. Fill remaining gaps with WorkTime and DriveTime, respecting constraints ---
                    currentProcessedTime = ts.StartDateTime; // Reset currentProcessedTime to actual day start for gap filling
                    Integer currentEntryIndex = 0;

                    while (currentProcessedTime < ts.EndDateTime) {
                        Datetime nextScheduledEntryStart = ts.EndDateTime;
                        Datetime nextScheduledEntryEnd = ts.EndDateTime;
                        TimeSheetEntry scheduledEntryToProcess = null;

                        for (Integer j = currentEntryIndex; j < currentDayEntries.size(); j++) {
                            if (currentDayEntries[j].StartTime >= currentProcessedTime) {
                                nextScheduledEntryStart = currentDayEntries[j].StartTime;
                                nextScheduledEntryEnd = currentDayEntries[j].EndTime;
                                scheduledEntryToProcess = currentDayEntries[j];
                                currentEntryIndex = j; 
                                break;
                            }
                        }
                        
                        if (currentProcessedTime < nextScheduledEntryStart) {
                            Integer availableMinutesInGap = (Integer) ((nextScheduledEntryStart.getTime() - currentProcessedTime.getTime()) / (1000 * 60));

                            while (availableMinutesInGap > 0) {
                                Integer durationMinutes = 0;
                                String category = '';

                                // Prioritize MeetingTime if not scheduled and enough space
                                if (!meetingScheduled && availableMinutesInGap >= meetingDuration) {
                                    category = 'MeetingTime';
                                    durationMinutes = meetingDuration;
                                    meetingScheduled = true;
                                    lastEntryWasWorkTime = false; 
                                } else if (lastEntryWasWorkTime) {
                                    // If last entry was WorkTime, the next MUST be DriveTime
                                    category = 'DriveTime';
                                    durationMinutes = Math.round(Math.random() * (maxDriveTimeDuration - minDriveTimeDuration)) + minDriveTimeDuration; // 5-30 mins
                                    durationMinutes = Math.min(durationMinutes, availableMinutesInGap);
                                    lastEntryWasWorkTime = false;
                                } else {
                                    // Generate WorkTime, ensure it has enough space for a subsequent DriveTime if needed
                                    Integer requiredMinBlock = minWorkTimeDuration;
                                    if (availableMinutesInGap > requiredMinBlock + minDriveTimeDuration) { 
                                       requiredMinBlock += minDriveTimeDuration;
                                    }

                                    if (availableMinutesInGap >= requiredMinBlock) {
                                        category = 'WorkTime';
                                        durationMinutes = Math.round(Math.random() * (maxWorkTimeDuration - minWorkTimeDuration)) + minWorkTimeDuration;
                                        durationMinutes = Math.min(durationMinutes, availableMinutesInGap);
                                        // Adjust WorkTime duration if it leaves too little space for DriveTime,
                                        // unless it's the last block before a scheduled entry or end of day
                                        if (availableMinutesInGap > durationMinutes && availableMinutesInGap - durationMinutes < minDriveTimeDuration) {
                                             if (availableMinutesInGap - minDriveTimeDuration >= minWorkTimeDuration) {
                                                 durationMinutes = availableMinutesInGap - minDriveTimeDuration;
                                             } else {
                                                 durationMinutes = availableMinutesInGap; // Take all available as WorkTime if no space for DriveTime
                                             }
                                        }
                                        lastEntryWasWorkTime = true;
                                    } else {
                                        // If not enough space for WorkTime + DriveTime, or just WorkTime,
                                        // take the remaining available time as WorkTime
                                        category = 'WorkTime';
                                        durationMinutes = availableMinutesInGap;
                                        lastEntryWasWorkTime = false; 
                                    }
                                }

                                if (durationMinutes <= 0) break; 

                                Datetime entryEndTime = currentProcessedTime.addMinutes(durationMinutes);
                                if (entryEndTime > nextScheduledEntryStart) {
                                    durationMinutes = (Integer) ((nextScheduledEntryStart.getTime() - currentProcessedTime.getTime()) / (1000 * 60));
                                    entryEndTime = nextScheduledEntryStart;
                                }

                                if (durationMinutes > 0) {
                                    currentDayEntries.add(new TimeSheetEntry(
                                        TimeSheetId = ts.Id,
                                        Status = 'New',
                                        StartTime = currentProcessedTime,
                                        EndTime = entryEndTime,
                                        Type = 'Direct',
                                        Category = category
                                    ));
                                }
                                currentProcessedTime = entryEndTime;
                                availableMinutesInGap = (Integer) ((nextScheduledEntryStart.getTime() - currentProcessedTime.getTime()) / (1000 * 60));
                            }
                        }

                        if (scheduledEntryToProcess != null) {
                            currentProcessedTime = nextScheduledEntryEnd;
                            currentEntryIndex++; 
                            if (scheduledEntryToProcess.Category != 'WorkTime' && scheduledEntryToProcess.Category != 'DriveTime') {
                                lastEntryWasWorkTime = false;
                            }
                        } else {
                            break; 
                        }
                    }

                    timeSheetEntriesToInsert.addAll(currentDayEntries);
                }

                // Insert all TimeSheetEntries for all days processed in this input
                if (!timeSheetEntriesToInsert.isEmpty()) {
                    insert timeSheetEntriesToInsert;
                }
                
                res.isSuccess = true;
                res.message = 'TimeSheets and TimeSheetEntries generated successfully for ' + input.serviceResourceExternalId + ' from ' + input.startDate + ' to ' + input.endDate + '.';
                // Optionally return the ID of the first TimeSheet created (or null if none)
                if (!timeSheetsToInsert.isEmpty()) {
                    res.timeSheetId = timeSheetsToInsert[0].Id;
                }
                results.add(res);

            } catch (Exception ex) {
                res.message = 'Error generating TimeSheets for ' + input.serviceResourceExternalId + ': ' + ex.getMessage() + ' at line ' + ex.getLineNumber();
                System.debug('Error: ' + res.message);
                System.debug('Stack Trace: ' + ex.getStackTraceString());
                results.add(res);
            }
        }
        return results;
    }
}