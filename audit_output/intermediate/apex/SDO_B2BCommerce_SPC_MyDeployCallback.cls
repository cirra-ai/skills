public with sharing class SDO_B2BCommerce_SPC_MyDeployCallback implements Metadata.DeployCallback {
    public void handleResult(Metadata.DeployResult result,
                             Metadata.DeployCallbackContext context) {
        Id jobId = context.getCallbackJobId();

        
        switch on (result.status) {
            when Succeeded {
                // Deployment was successful
            }
            when SucceededPartial {
                // The deployment succeeded, but some components might not have been successfully deployed. Check Metadata.DeployResult for more details.
            }
            when Failed {
                // Deployment was not successful
            }
            when Canceled {

            }
            when Pending, InProgress, Canceling {
                // Queued or state changing
            }
        }
    }
}