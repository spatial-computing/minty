!function() {
    function objectifyForm(formArray) {//serialize data function
      var returnArray = {};
      for (var i = 0; i < formArray.length; i++){
        returnArray[formArray[i]['name']] = formArray[i]['value'];
      }
      return returnArray;
    }

    $('#add-new-type-form').on('submit',function (event) {
        event.preventDefault();
        let type = $(this).find('.is-update').val() === 'no' ? 'add' : 'update';
        let format = 'type';
        let former = $(this).find('.former-value').val();
        let value = $(this).find('[name=name]').val();
        let csrf_token = $(this).find('[name=csrf_token]').val();
        if (value == '') {
            return;
        }
        $.ajax({
            url: '/viztype',
            type: 'POST',
            dataType: 'json',
            data: {type:type, format:format, former:former, value:value, csrf_token:csrf_token}
        }).done(function (json) {
            window.location.reload();
            // if (json.status === 'ok' && type === 'add') {

            // }else if (json.status === 'ok' && type === 'update'){

            // }
        });
    });
    $('.add-new-key-form').on('submit', function (event) {
        event.preventDefault();
        let data = objectifyForm($(this).serializeArray());
        data['type'] = data['is-update'] === 'no' ? 'add' : 'update';
        data['format'] = 'key';
        data['former'] = data['former-value'];
        if (data['value'] == '') {
            return;
        }
        $.ajax({
            url: '/viztype',
            type: 'POST',
            dataType: 'json',
            data: data
        }).done(function (json) {
            window.location.reload();
        })
    });
    $('.type-close').on('click', function (event) {
        event.preventDefault();
        let name = $(this).data('name');
        let type = "type";
        let csrf = $(this).data('csrf');

        $.ajax({
            url: '/viztype',
            type: 'DELETE',
            dataType: 'json',
            data: {name: name, type: type, csrf_token: csrf}
        }).done(function (json) {
            window.location.reload();
        });
    });
    $('.key-close').on('click', function (event) {
        event.preventDefault();
        let name = $(this).data('name');
        let belongto = $(this).data('belongto');
        let csrf = $(this).data('csrf');
        let type = "key";
        $.ajax({
            url: '/viztype',
            type: 'DELETE',
            dataType: 'json',
            data: {name: name, belongto: belongto, type: type, csrf_token: csrf}
        }).done(function (json) {
            window.location.reload();
        });
    });
    $('.type-modify').on('click', function (event) {
        event.preventDefault();
        let name = $(this).data('name');
        $('#add-new-type-form').find('.viz-type-name').val(name);
        $('#add-new-type-form').find('.is-update').val('yes');
        $('#add-new-type-form').find('.former-value').val(name);
        $('#add-new-type-form').find('[type=submit]').val('modify ' + name);
        $('#btn-add-enable').removeClass('disabled');
        $(document).scrollTop($("#add-card").offset().top);
    });
    $('#btn-add-enable').on('click', function (event) {
        event.preventDefault();
        $('#add-new-type-form').find('.viz-type-name').val('');
        $('#add-new-type-form').find('.is-update').val('no');
        $('#add-new-type-form').find('.former-value').val('');
        $('#add-new-type-form').find('[type=submit]').val('Add new viz type');
        $(this).addClass('disabled');
    });
    $('.key-modify').on('click', function (event) {
        event.preventDefault();
        let type_idx = $(this).data('type-index');
        $(this).addClass('disabled');
// data-name="{{ metadata.name }}"  data-belongto="{{ viztype.name }}" data-placeholder="{{ metadata.placeholder }}" data-htmltag="{{ metadata.htmltag }}" data-description="{{ metadata.description }}" data-options="{{ metadata.options }}" 
        let name = $(this).data("name");
        let belongto = $(this).data('belongto');
        let placeholder = $(this).data('placeholder');
        let htmltag = $(this).data('htmltag');
        let description = $(this).data('description');
        let options = $(this).data('options');

        let btn = $('#collapseAddNewKeyBtn-' + type_idx);
        btn.html("Modify " + name + " of " + belongto);
        $('#collapseAddNewKey-' + type_idx).addClass('show');

        $('#collapseAddNewKey-' + type_idx).find('[name=value]').val(name);
        $('#collapseAddNewKey-' + type_idx).find('[name=placeholder]').val(placeholder);
        $('#collapseAddNewKey-' + type_idx).find('[name=htmltag]').val(htmltag);
        $('#collapseAddNewKey-' + type_idx).find('[name=description]').val(description);
        $('#collapseAddNewKey-' + type_idx).find('[name=options]').val(options);
        $('#collapseAddNewKey-' + type_idx).find('[name=is-update]').val('yes');
        $('#collapseAddNewKey-' + type_idx).find('[name=former-value]').val(name);
        $('#collapseAddNewKey-' + type_idx).find('[type=submit]').val("Modify " + name);

    });
    $('.btn-add-key-enable').on('click', function (event) {
        event.preventDefault();
        let name = $(this).data("name");

        $(this).removeClass('disabled');
        $(this).parents('.list-group-item').find('[name=value]').val('');
        $(this).parents('.list-group-item').find('[name=placeholder]').val('');
        $(this).parents('.list-group-item').find('[name=htmltag]').val('');
        $(this).parents('.list-group-item').find('[name=description]').val('');
        $(this).parents('.list-group-item').find('[name=options]').val('');
        $(this).parents('.list-group-item').find('[name=is-update]').val('no');
        $(this).parents('.list-group-item').find('[name=former-value]').val('');
        $(this).parents('.list-group-item').find('[type=submit]').val("Add metadata-key to  " + name);
        $(this).parents('.list-group-item').find('button.addbtn').html('Add New Key to ' + name);
    })
}();