!(function () {
    console.log( "ready!" );
    // $('#dtHorizontalExample').DataTable({
    // "scrollX": true
    // });
    

    $('.run-btn').on('click',function (event) {
        event.preventDefault();   
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
        console.log(bash)
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
            //     url:'/bash/view/',
            //     type:'POST',
            //     dataType: 'json',
            //     data: bash
            // }).done(function(json){
            //     window.location.reload()
            // });           
        }
    });

    var badge = {
        finished: '<span class="badge badge-success text-wrap">Finished</span>',
        queued: '<span class="badge badge-info text-wrap">Queued</span>',
        started: '<span class="badge badge-warning text-wrap">Started</span>',
        failed: '<span class="badge badge-danger text-wrap">Failed</span>',
        '': '<span class="badge badge-dark text-wrap">Not running</span>'
    }
    var job_status_tr_class = {
        finished: 'table-success',
        queued: 'table-info',
        started: 'table-info',
        failed: 'table-warning',
        '': 'table-light'   
    }
    function updateStatus() {
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
                $($(document).find('.bash-status')[i]).html( badge[json.job_status[i]] )
                $($(document).find('.bash-status')[i]).parents('tr').removeClass().addClass(job_status_tr_class[json.job_status[i]]);
                if(json.job_status[i]==='queued' || json.job_status[i]==='started'){
                   $($(document).find('.run-btn')[i]).prop('disabled', true);
                }
                else {
                   $($(document).find('.run-btn')[i]).prop('disabled', false); 
                }
            }
            
        });
    }
    updateStatus();
    var handle = setInterval(function () {
        updateStatus();
    }, 10000);

    $('.status-btn').on('click',function(evnet){
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{jobid:$(this).data('rqid'),bashid:$(this).data('bashid'),csrf_token:$(this).data('csrf')},
        }).done(function(json){
            $('#bash-modal .modal-body').html(json.exc_info);
            $('#bash-modal .bash-modal-status').html(badge[json.job_status]);
            // console.log("json.job_status")
        })
    });


    $('.setting-form').on('submit',function(event){
        event.preventDefault();
        let setting = $( this ).serialize();
        $.ajax({
            url: '/bash',
            type: 'POST',
            dataType: 'json',
            data: setting
        }).done(function (json) {
            window.location.reload();
        });       


    })

}());
