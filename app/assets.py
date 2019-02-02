from flask_assets import Bundle

def create_assets(assets):
    # js = Bundle(
    #     'js/viztype.js',
    #     output='js/viztype_libs.js'
    # )
    # assets.register('JS_FRAMEWORS', js)
    js = Bundle(
        'js/bash.js',
        filters='jsmin', 
        output='js/bash_libs.js'
    )
    assets.register('JS_FRAMEWORS_BASH', js)
    
    js = Bundle(
        'js/viztype.js',
        filters='jsmin', 
        output='js/viztype_libs.js'
    )
    assets.register('JS_FRAMEWORS_VIZTYPE', js)

    css = Bundle(
        'css/sticky-footer.css',
        filters='cssmin',
        output='css/min.css'
    )
    assets.register('CSS_FRAMEWORKS', css)