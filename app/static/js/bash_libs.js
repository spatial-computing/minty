!(function () {
 
    

    $('.run-btn').on('click',function (event) {
        event.preventDefault();   
        let command = $(this).data('command');
        let confirmation = confirm("This action will overwrite the database and may redownload files, are you sure?");
        if (confirmation) {
            $.ajax({
                url: '/bash/run',
                type: 'POST',
                dataType: 'json',
                data: {command:command, csrf_token:$('.run-btn').data('csrf'),bashid:$(this).data('bashid')}
            }).done(function (json) {
                alert(json.status);
                updateStatus();
            });
        }
        
    });
    $('.cancel-btn').on('click',function (event) {
        event.preventDefault();   
        let confirmation = confirm("This action will cancel this job, are you sure?");
        if (confirmation) {
            $.ajax({
                url: '/bash/cancel',
                type: 'POST',
                dataType: 'json',
                data: { 
                    csrf_token: $('.run-btn').data('csrf'),
                    bashid: $(this).data('bashid')}
            }).done(function (json) {
                alert(json.status);
                updateStatus();
            });

        }
        
    });

    var badge = {
        finished: '<span class="badge badge-info text-wrap">Finished</span>',
        downloading: '<span class="badge badge-dark text-wrap">Downloading</span>',
        success: '<span class="badge badge-success text-wrap">Success</span>',
        ready_to_run: '<span class="badge badge-info text-wrap">Ready to run</span>',
        running: '<span class="badge badge-warning text-wrap">Runnnig</span>',
        failed: '<span class="badge badge-danger text-wrap">Failed</span>',
        not_enqueued: '<span class="badge badge-dark text-wrap">Not enqueued</span>',
        not_found: '<span class="badge badge-dark text-wrap">Not Found</span>'
    }
    var job_status_tr_class = {
        finished: 'table-success',
        downloading: 'table-info',
        success: 'table-success',
        ready_to_run: 'table-warning',
        running: 'table-info',
        failed: 'table-danger',
        not_enqueued: 'table-light',
        not_found: 'table-light'
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
            for (var i = 0; i < json.status.length; i++) {
                $($(document).find('.bash-status')[i]).html( badge[json.status[i]] )
                $($(document).find('.bash-status')[i]).parents('tr').removeClass().addClass(job_status_tr_class[json.status[i]]);
                if(json.status[i] === 'running'){
                   $($(document).find('.run-btn')[i]).hide(); 
                   $($(document).find('.cancel-btn')[i]).show();
                }else {
                    $($(document).find('.run-btn')[i]).show();
                    $($(document).find('.cancel-btn')[i]).hide(); 
                }
            }
            
        });
    }
    updateStatus();
    var handle = setInterval(function () {
        updateStatus();
    }, 10000);
    function escape_html(string) {
        return string.replace(/&/g, "&amp;").replace(/>/g, "&gt;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
    }
    $('.status-btn').on('click',function(evnet){
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{
                jobid: $(this).data('rqid'),
                bashid: $(this).data('bashid'),
                download_id: $(this).data('download-id'),
                csrf_token: $(this).data('csrf')
            },
        }).done(function(json){
            $('#bash-modal .running-log .bash-modal-status').html(badge[json.status]);
            $('#bash-modal .modal-body #nav_exc_info pre').html(json.logs.exc_info === null ? "No exc info" : escape_html(json.logs.exc_info));
            $('#bash-modal .modal-body #nav_error pre').html(escape_html(json.logs.error))
            $('#bash-modal .modal-body #nav_output pre').html(escape_html(json.logs.output));

            $('#bash-modal .download-log .bash-modal-status').html(badge[json.download_status]);
            $('#bash-modal .modal-body #nav_download_exc_info pre').html(escape_html(json.download_logs.exc_info));
            $('#bash-modal .modal-body #nav_download_error pre').html(escape_html(json.download_logs.error))
            $('#bash-modal .modal-body #nav_download_output pre').html(escape_html(json.download_logs.output));
            // console.log("json.job_status")
            // console.log(json.logs)
        })
    });


    // $('.setting-form').on('submit',function(event){
    //     event.preventDefault();
    //     let setting = $( this ).serialize();
    //     console.log(setting)
    //     $.ajax({
    //         url: '/bash',
    //         type: 'POST',
    //         dataType: 'json',
    //         data: setting
    //     }).done(function (json) {
    //         window.location.reload();
    //     });       

    // })
    $('.custom-setting').on('change',function(event){
        event.preventDefault();
        let status = $(this).prop("checked");
        let name = $( this ).attr('name');
        let csrf_token = $('#csrf_token_hidden').val();
        $(this).prop("checked",status);
        $.ajax({
            url:'/bash/defaultsetting',
            type:'POST',
            dataType:'json',
            data:{csrf_token:csrf_token, status:status, name:name}
        }).done(function(json){
            // window.location.reload();
            $('.toast-body').html(json.name +" changed to " +json.status)
            $('.toast').toast('show');

        })
    });
    $('.custom-controller').on('change',function(event){
        event.preventDefault();
        let status = $(this).prop("checked");
        let name = $( this ).attr('name');
        let csrf_token = $('#csrf_token_hidden').val();
        $(this).prop("checked",status);
        $.ajax({
            url:'/bash/defaultsetting/controller',
            type:'POST',
            dataType:'json',
            data:{csrf_token:csrf_token, status:status, name:name}
        }).done(function(json){
            // window.location.reload();
            $('.toast-body').html(json.name +" changed to " +json.status)
            $('.toast').toast('show');

        })
    });

}());
