# Generated by Django 3.0.1 on 2020-04-11 03:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20200411_0249'),
    ]

    migration = """
CREATE FUNCTION recipes_trigger() RETURNS trigger AS $$
begin
    new.search_vector :=
        setweight(to_tsvector('pg_catalog.english', coalesce(new.title,'')), 'A') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(new.ingredients_text,'')), 'B') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(new.instructions_text,'')), 'B');
    return new;
end
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON recipes_recipe FOR EACH ROW EXECUTE PROCEDURE recipes_trigger();
    """

    reverse_migration = '''
DROP TRIGGER tsvectorupdate ON recipes_recipe;
    '''

    operations = [
        migrations.RunSQL(migration, reverse_migration)
    ]
