# Database backup, restore and rollback (MedSync, MySQL 8)

These notes cover how to save the `medsync` database, bring it back, and undo a change that went wrong.
Commands are for Windows PowerShell from the project root. Replace `root` with your MySQL user.

## 0. One-time setup: find the MySQL tools

`mysqldump` and `mysql` live in the MySQL Server `bin` folder. If PowerShell says the command is not recognised, either add the folder to your PATH or call the tool by its full path, for example:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" --version
```

Backups can contain real data, so the `backups/` folder is listed in `.gitignore` and must never be committed.

## 1. Back up

```powershell
mkdir backups -Force
mysqldump -u root -p --single-transaction --routines --result-file="backups\medsync_2026-11-22.sql" medsync
```

- `--single-transaction` takes a consistent copy without locking the tables.
- Use `--result-file` instead of `>`: in Windows PowerShell, `>` saves the file in a format MySQL cannot read back.
- Put the date in the file name so older backups are not overwritten.

You can also use MySQL Workbench: **Server > Data Export**, choose `medsync`, "Export to Self-Contained File".

## 2. Restore

```powershell
cmd /c "mysql -u root -p medsync < backups\medsync_2026-11-22.sql"
```

(`cmd /c` is needed because PowerShell does not support the `<` operator.) The database must already exist; if it does not, run `database\schema.sql` first (section 3). In Workbench, use **Server > Data Import** instead.

Check the restore worked:

```powershell
mysql -u root -p -e "SELECT COUNT(*) FROM medsync.medicines;"
```

## 3. Rebuild from scratch (repeatable reset)

`database/schema.sql` drops every table (`DROP TABLE IF EXISTS`, in dependency order) and recreates it, and `database/seed.sql` reloads the demo data. This is the project's repeatable migration/reset step:

```powershell
cmd /c "mysql -u root -p < database\schema.sql"
cmd /c "mysql -u root -p medsync < database\seed.sql"
```

Warning: this deletes all current data in `medsync`. Take a backup first (section 1) if the data matters.

## 4. Rollback after a failed change

**Inside the application:** every database write runs through `transaction()` in `db.py`. If anything fails, the whole write is rolled back automatically and the error is logged, so a failed order or delivery update never leaves half-saved data.

**When changing the schema by hand (for example adding a column):**

1. Back up (section 1).
2. Apply the change in a copy of the script or in Workbench.
3. Run the app and the tests (`python -m pytest tests/`).
4. If anything breaks, restore the backup (section 2), or rebuild from `schema.sql` and `seed.sql` (section 3) if only demo data was in use.
5. Fix the change and try again.

For code changes, `git revert <commit>` undoes a bad commit without rewriting history.
