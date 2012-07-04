README for the Zope CookieUserFolder Product

  The CookieUserFolder is a replacement for a Zope user folder. It does 
  everything the bog-standard Zope user folder does, but using cookies 
  and login/logout-screens instead of the standard basic HTTP auth.
 
  For more information about the CookieUserFolder please visit 
  http://www.dataflake.org/software/cookieuserfolder/


  **Requirements**

    In order for this product to run you will need to provide the 
    following items:

    * A running Zope site version 2.3 or higher


  **Tested Platforms and versions**

    This product has been written on and for Zope 2.3.0 and up. I am 
    not going to support earlier versions of Zope with my product.


  **Custom login page**
 
    Check out the code in the Cookie User Folder install directory
    under dtml/login.dtml for what a login page has to do. You
    want to make sure that you have a *form* which posts at
    least 2 input fields named *__ac__name* (user name) and
    *__ac_password* (password).
 
    You can make your custom page the default page by simply
    instantiating it under the "Contents" tab of the
    Cookie User Folder and giving it an id of *login*.


  **Help, I locked myself out of my own site!**
 
    This can happen if you create a custom login page within
    the Cookie User Folder which does not do the right thing.
 
    In order to authenticate you can force the usage of the
    default login page by going to:
 
    http://path/to/acl_users/docLogin
 
    Type in your name and password and hit the button. You
    will stay on the same page, even if the authentication
    succeeded, you can then type the desired address into your
    browser's navigation bar.


  **Logging out**

    Logging out and expiring the authentication cookie can be 
    achieved by calling the "logOut" method on the Cookie User Folder.

    You can either construct a simple link to it like this::
    
      <a href="/path/to/acl_users/logOut">Log Me OUT!</a>

    Or you can use a simple form that posts to that same URL::

      <form taget="/path/to/acl_users/logOut" method="post">
        <input type="submit" value=" Log Me OUT! ">
      </form>

    Logging out will lead you to the logout-screen. In order to 
    customize this screen simply drop an object with the ID "logout"
    into the Cookie User Folder. It can be a page or a method that 
    performs a redirect elsewhere. There are no special requirements
    like there are for the login page.


  **Migrating user accounts**

    If you want to replace a standard Zope user folder with a Cookie
    User Folder the package now includes a script to migrate user
    accounts from the old to the new user folder. This script will
    only work with standard Zope user folders, not with any third-
    party user-folderish objects. Here is how to use it:

      o You must be logged in as the super user, you will lock
        yourself out if you try this as a user from the user folder
        you are about to delete! 
        
        If you don't have a super user account yet create it now 
        using either zpasswd.py or putting a colon-separated 
        username:password into a simple text file named "access" at 
        the root of your Zope installation on the file system. 
        
        You must restart Zope at that point so it reads the file, then 
        log in using the superuser name and password.

      o In the folder that contains the old user folder instantiate
        an "External Method" from the add list and give it the
        following values:

          o id: whatever you want

          o Module Name: CookieUserFolder.ReplaceUserFolder

          o Function Name: replace

      o Hit "Add"

      o Click on the new external method object and run it using
        the "Test" tab. You will see some diagnostic output.

    At this point your old user folder will be a Cookie User Folder 
    and if you want to see your old user accounts just open it and 
    hit the "Contents" tab.

    **Disclaimer**

      Use this script at your own risk or test it beforehand on 
      a copy of your old user folder. The script has been tested but 
      in a limited fashion (I have no large user folder to test it 
      with).

    
