# does the opposite of make_backup.sh
# copies the contents of the backup directory to the current directory

backup_name=$1

current_dir=workspace/$backup_name/
backup_dir=workspace/backup/$backup_name

# Copy the contents of the backup directory to the current directory
rm -rf $current_dir
mkdir -p $current_dir
cp -r $backup_dir/* $current_dir/
