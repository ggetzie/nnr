import recipes.models as rModels
import main.models as mModels

def migrate_recipes():
    mRecipes = mModels.Recipe.objects.all()
    for mRecipe in mRecipes:
        rRecipe = rModels.Recipe(title=mRecipe.title,
                                 ingredients_text=mRecipe.ingredients_text,
                                 instructions_text=mRecipe.instructions_text,
                                 user=mRecipe.user,
                                 featured=mRecipe.featured,
                                 last_featured=mRecipe.last_featured)
        rRecipe.save()

def migrate_tags():        
    mTags = mModels.Tag.objects.all()
    for mTag in mTags:
        rTag = rModels.Tag(name=mTag.name)
        rTag.save()    

def migrate_usertags():
    mUserTags = mModels.UserTag.objects.all()
    for mUserTag in mUserTags:
        rTag = rModels.Tag.objects.get(name_slug=mUserTag.tag.name_slug)
        rRecipe = rModels.Recipe.objects.get(title_slug=mUserTag.recipe.title_slug)
        rUserTag = rModels.UserTag(user = mUserTag.user,
                                   tag=rTag,
                                   recipe=rRecipe)
        rUserTag.save()    

def migrate_reciperatings():        
    mRecipeRatings = mModels.RecipeRating.objects.all()
    for mRecipeRating in mRecipeRatings:
        rRecipe = rModels.Recipe.objects.get(title_slug=mRecipeRating.recipe.title_slug)
        rRecipeRating = rModels.RecipeRating(recipe=rRecipe,
                                             user=mRecipeRating.profile.user,
                                             rating=mRecipeRating.rating)
        rRecipeRating.save()                                                     

def migrate_all():
    migrate_recipes()
    migrate_tags()
    migrate_usertags()
    migrate_reciperatings()

    
