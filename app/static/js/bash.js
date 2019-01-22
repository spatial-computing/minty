!(function () {
    console.log( "ready!" );
    // $('#dtHorizontalExample').DataTable({
    // "scrollX": true
    // });
    

    $('.run-btn').on('click',function (event) {
        event.preventDefault();
        console.log('sss');    
        let command = $(this).data('command');
        $.ajax({
            url: '/bash/run',
            type: 'POST',
            dataType: 'json',
            data: {command:command, csrf_token:$('.run-btn').data('csrf'),bashid:$(this).data('bashid')}
        }).done(function (json) {
            window.location.reload();
        });
    });

    $('.bashform').on('submit', function (event){
        event.preventDefault();
        let bash=$( this ).serialize();
        if ($('.submit').data('action')=='add'){
            $.ajax({
                url:'/bash/add',
                type:'POST',
                dataType: 'json',
                data: bash
            }).done(function(json){
                window.location.reload()
            });
        }
        else {
            // $.ajax({
            //     url:'/bash/add',
            //     type:'POST',
            //     dataType: 'json',
            //     data: bash
            // }).done(function(json){
            //     window.location.reload()
            // });           
        }
    });

}());
