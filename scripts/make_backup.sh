backup_name=$1

current_dir=workspace/$backup_name/
# Create the backup directory as workspace/backup/backup_name
backup_dir=workspace/backup/$backup_name

# Create the backup directory if it doesn't exist
mkdir -p $backup_dir

# Copy the contents of the current directory to the backup directory
cp -r $current_dir/* $backup_dir/