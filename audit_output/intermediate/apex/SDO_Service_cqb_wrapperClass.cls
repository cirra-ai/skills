public class SDO_Service_cqb_wrapperClass{
    @auraenabled
    public Contact c;
    @auraenabled
    public User u;
   
    public SDO_Service_cqb_wrapperClass(User myUser, Contact myContact){
        this.u = myUser;
        this.c = myContact;
    }
}