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

    var badge = {
        finished: '<span class="badge badge-success">Finished</span>',
        queued: '<span class="badge badge-info">Queued</span>',
        started: '<span class="badge badge-warning">Started</span>',
        failed: '<span class="badge badge-danger">Failed</span>',
        '': '<span class="badge badge-dark">Not running</span>'
    }
    var handle = setInterval(function () {
        console.log($(document).find('#bash_rqids').val())
        console.log($(document).find('#bash_ids').val())
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{
                type: 'batch',
                jobid: $(document).find('#bash_rqids').val(), 
                bashid: $(document).find('#bash_ids').val(), 
                csrf_token: $(document).find('#csrf_token_hidden').val()
            },
        }).done(function(json){
            for (var i = json.job_status.length - 1; i >= 0; i--) {
                $($(document).find('.bash-status')[i]).html(badge[json.job_status[i]])
            }
            
        })
    }, 1000);

    $('.status-btn').on('click',function(evnet){
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{jobid:$(this).data('rqid'),bashid:$(this).data('bashid'),csrf_token:$(this).data('csrf')},
        }).done(function(json){
            $('.modal-body').html(json.job_status);
            console.log("json.job_status")
        })
    });

}());
