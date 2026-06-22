Recovery info
To create a backup of the database:

1. Render dashboard and SEARCH For meckmeier (this is the database service)
2. Use the Recovery page EXPORT a backup file.
3. Download the file to the c:\projects\db_backups folder.
4. You can extract the data.

To Restore a database:
I created a database on my local pgAdmin which was called restore_test.
Then i issued this command:

1. pg_restore -U postgres -Fd -d restore_test  "C:\Project\db_backup\2026-06-22T15_14Z.dir\2026-06-22T15_14Z\naturalist_db" > restore.log 2>&1

2. Password is for my local pgAdmin -- which is postgre; and password1.

scenario - bad import on 6/15... i did a deployment on 6/19 (and didn't know about the bad import). Now i need to go back. 6/19 - included a database change. previous code base was deployed on 6/1. now to fix the problem: revert code base to the state it was in on 6/15 (that would be the 6/1 code base). so pull that specific commit and deploy on render. then restore the database on 6/14. now the database should be before my last code change. Check everything. Make sure it's right. even wait a day or so. then redeploy 6/19 code change.