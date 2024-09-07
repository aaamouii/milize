from utils.checks import check_connection

class Series:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    @check_connection
    def new(self, group_id, name, drive_link, style_guide, mangadex, thumbnail):
        try:
            self.cursor.execute("INSERT INTO series (series_name, series_drive_link, style_guide, group_id, mangadex, thumbnail) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (series_name) DO NOTHING RETURNING series_id;", (name, drive_link, style_guide, group_id, mangadex, thumbnail))
            self.connection.commit()

            series_id = self.cursor.fetchone()

            if series_id:
                print(f"New series '{name}' added with ID {series_id[0]}.")
                return series_id[0]
            else:
                print(f"Series '{name}' already exists.")
                return None

        except Exception as e:
            self.connection.rollback()
            print(f"Failed to add new series: {e}")
            return None

    @check_connection
    def get(self, group_name, series_name):
        try:
            query = """
                SELECT s.series_id, s.series_name, s.series_drive_link, s.style_guide, s.mangadex, g.group_id, g.group_name, s.thumbnail, s.is_archived
                FROM series s
                JOIN groups g ON s.group_id = g.group_id
                WHERE g.group_name = %s AND s.series_name = %s;
            """

            self.cursor.execute(query, (group_name, series_name))
            self.connection.commit()
            return self.cursor.fetchone()
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to select series '{series_name}' from group '{group_name}': {e}")
            return []

    @check_connection
    def delete(self, group_name, series_name):
        try:
            query = """
                DELETE FROM series
                USING groups
                WHERE series.group_id = groups.group_id
                AND groups.group_name = %s
                AND series.series_name = %s;
            """
            self.cursor.execute(query, (group_name, series_name))
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to delete series '{series_name}' from group '{group_name}': {e}")
            return None

    @check_connection
    def get_by_id(self, series_id):
        try:
            self.cursor.execute("SELECT * FROM series WHERE series_id = %s", (series_id,))
            self.connection.commit()
            return self.cursor.fetchone()
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to select series '{series_id}': {e}")
            return []

    @check_connection
    def move(self, series_id, group_from_id, group_to_id):
        try:
            self.cursor.execute("UPDATE series SET group_id = %s WHERE group_id = %s", (group_to_id, group_from_id))
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to move series with ID '{series_id}' from group '{group_from_id}' to group '{group_to_id}': {e}")
            return None

    @check_connection
    def get_by_group_id(self, group_id):
        try:
            self.cursor.execute("SELECT series_id, series_name, series_drive_link, style_guide, mangadex, group_id FROM series WHERE group_id = %s", (group_id,))
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to select all series from group: {e}")
            return []

    @check_connection
    def get_by_group_name(self, group_name):
        try:
            query = """
                SELECT s.series_id, s.series_name, s.series_drive_link, s.style_guide, s.mangadex, g.group_id
                FROM series s
                JOIN groups g ON s.group_id = g.group_id
                WHERE g.group_name = %s AND s.is_archived = FALSE;
            """
            self.cursor.execute(query, (group_name,))
            return self.cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to select all series from group: {e}")
            return []

    @check_connection
    def update(self, series_name, new_name = None, new_drive_link = None, new_style_guide = None, new_mangadex = None, new_thumbnail = None):
        updates = []
        params = []

        if new_name:
            updates.append("series_name = %s")
            params.append(new_name)
        if new_drive_link:
            updates.append("series_drive_link = %s")
            if new_drive_link.lower() == 'none':
                params.append(None)
            else:
                params.append(new_drive_link)
        if new_style_guide:
            updates.append("style_guide = %s")
            if new_style_guide.lower() == 'none':
                params.append(None)
            else:
                params.append(new_style_guide)
        if new_mangadex:
            updates.append("mangadex = %s")
            if new_mangadex == 'none':
                params.append(None)
            else:
                params.append(new_mangadex)

        if new_thumbnail:
            updates.append("thumbnail = %s")
            if new_thumbnail == 'none':
                params.append(None)
            else:
                params.append(new_thumbnail)
        
        if updates:
            params.append(series_name)

            try:
                self.cursor.execute(f"UPDATE series SET {', '.join(updates)} WHERE series_name = %s", tuple(params))
                self.connection.commit()
                return self.cursor.rowcount
            except Exception as e:
                self.connection.rollback()
                print(f"Failed to update series {series_name}: {e}")
                return None
        return 0

    @check_connection
    def count_chapters(self, series_name, count_archived = False):
        try:
            query = """
            SELECT COUNT(*) AS chapter_count
            FROM chapters c
            JOIN series s ON c.series_id = s.series_id
            WHERE s.series_name = %s
            """

            if not count_archived:
                query += " AND c.is_archived = FALSE"

            self.cursor.execute(query, (series_name,))
            self.connection.commit()
            return self.cursor.fetchone().chapter_count
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to count chapters for series '{series_name}': {e}")
            return None

    @check_connection
    def archive(self, series_id):
        try:
            self.cursor.execute("UPDATE series SET is_archived = TRUE WHERE series_id = %s", (series_id,))
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to archive series with ID '{series_id}': {e}")
            return None

    @check_connection
    def unarchive(self, series_id):
        try:
            self.cursor.execute("UPDATE series SET is_archived = FALSE WHERE series_id = %s", (series_id,))
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Failed to unarchive series with ID '{series_id}': {e}")
            return None