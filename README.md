<a href="https://extensionerp.com"><img src="https://cdn.extensionmart.com/Extension-ERP-06-32.png" align="right" /></a>

## Frappe Digital Ocean Spaces Attachment Integration

Frappe app to make file upload automatically upload and read from Spaces.

#### Features.

1. Upload both public and private files to Spaces.
2. Stream files from Spaces, when file is viewed everytime.
3. Lets you add Spaces credentials
    (spaces key, spaces secret, space name, folder name) through ui and migrate existing
    files.
4. Deletes from Spaces whenever a file is deleted in ui.
5. Files are uploaded categorically in the format.
    {Spaces_folder_path}/{year}/{month}/{day}/{doctype}/{file_hash}

#### Installation.

1. bench get-app https://github.com/extension-technologies/Frappe-attachments-s3.git
2. bench install-app frappe_s3_attachment

#### Configuration Setup.

1. Open single doctype "s3 File Attachment"
2. Enter (space Name, spaces key, spaces secret, Spaces space Region name, Folder Name)
    Folder Name- folder name is the default folder path in Spaces.
3. Migrate existing files lets all the existing files in private and public folders
    to be migrated to Spaces.
4. Delete From Cloud when selected deletes the file form Spaces space whenever a file
    is deleted from ui. By default the Delete from cloud will be unchecked.

#### License

MIT
