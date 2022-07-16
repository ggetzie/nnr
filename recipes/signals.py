import logging
import pathlib
import subprocess
import shutil

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from recipes.models import RecipePhoto, Tag, recipe_photo_path, tag_photo_path

PHOTOS = "/usr/local/src/nnr/awslambda/photos/build/photos"
logger = logging.getLogger(__name__)


def is_newer(photo):
    """Check if the original uploaded photo was added more recently than anything else in its directory"""
    files = list(photo.parent.iterdir())
    if len(files) == 1:
        return True
    for f in files:
        if photo != f and (photo.stat().st_mtime > f.stat().st_mtime):
            return True
    return False


def run_photos(filepath):
    input_file = str(filepath)
    output_dir = str(filepath.parent)
    res = subprocess.run(
        [PHOTOS, "--local", f"--input={input_file}", f"--output={output_dir}"]
    )
    return res


@receiver(post_save, sender=RecipePhoto)
def optimize_recipephoto(sender, **kwargs):
    """
    Resize and optimize photos saved locally during debug.
    In production this is handled by an aws lambda.
    """
    if settings.DEBUG:
        rp = kwargs["instance"]
        logger.info(f"Optimizing recipe photo {rp.id}")
        filepath = pathlib.Path(rp.photo.file.name)
        if is_newer(filepath):
            res = run_photos(filepath)
            print(res)


@receiver(post_save, sender=Tag)
def optimize_tagphoto(sender, **kwargs):
    tag = kwargs["instance"]
    # This doesn't work. Can't find the file if the photo field has been cleared
    # need to delete unused photos at a different point
    # if not tag.photo:
    #     # remove media files if photo cleared from tag.
    #     tag.photo.storage.delete(tag.photo.file.name)
    #     if settings.DEBUG:
    #         folder = pathlib.Path(
    #             settings.MEDIA_ROOT, tag_photo_path(tag, "orig.jpeg")
    #         ).parent
    #         logger.info(f"removing {folder}")
    #         shutil.rmtree(folder)
    #     return

    if settings.DEBUG and tag.photo:
        logger.info(f"Optimizing tag photo {tag.name}")
        filepath = pathlib.Path(tag.photo.file.name)
        if is_newer(filepath):
            res = run_photos(filepath)
            print(res)


@receiver(post_delete, sender=Tag)
def cleanup_tagphoto(sender, **kwargs):
    tag = kwargs["instance"]
    if tag.photo and tag.photo != "":
        tag.photo.storage.delete(tag.photo.file.name)
    if settings.DEBUG:
        folder = pathlib.Path(
            settings.MEDIA_ROOT, tag_photo_path(tag, "orig.jpeg")
        ).parent
        logger.info(f"removing {folder}")
        shutil.rmtree(folder)


@receiver(post_delete, sender=RecipePhoto)
def cleanup_recipephoto(sender, **kwargs):
    rp = kwargs["instance"]
    if rp.photo and rp.photo != "":
        rp.photo.storage.delete(rp.photo.file.name)
    if settings.DEBUG:
        folder = pathlib.Path(
            settings.MEDIA_ROOT, recipe_photo_path(rp, "orig.jpeg")
        ).parent
        logger.info(f"removing {folder}")
        shutil.rmtree(folder)
