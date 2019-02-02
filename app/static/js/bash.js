!(function () {
    var container = document.getElementById("jsoneditor");
    var options = {
        mode: 'form',
        sortObjectKeys: false,

    };
    var editor = new JSONEditor(container, options);
    function start_loading() {
        $('#loading-screen').css('display', 'flex');
    }
    function stop_loading() {
        $('#loading-screen').hide();   
    }


    $('.edit-register-metadata').on('click', function (event) {
        event.preventDefault();
        let self = this;
        start_loading();
        $.ajax({
            url: '/bash/edit_dc_metadata',
            type: 'POST',
            dataType: 'json',
            data: {
                csrf_token: $(self).data('csrf'),
                dataset_id: $(self).data('dataset-id'),
                viz_config: $(self).data('viz-config')
            }
        }).done(function (json) {
            
            if (json.status === 'ok') {
                editor.set(json.reg_info);
                editor.expandAll();
                stop_loading();
                $('#jsoneditor-modal').modal('show');
            }else{
                stop_loading();
                swal("Error Occurred!", "Can not fetch dataset info!", "error");
            }
            
        });
    });
    $('#jsoneditor-modal .save-changes').on('click', function (event) {
        event.preventDefault();
        let self = this;
        var reg_json = editor.get();
        $('#jsoneditor-modal').modal('hide');
        start_loading();
        $.ajax({
            url: '/bash/register_dc_metadata',
            type: 'POST',
            dataType: 'json',
            data: {
                csrf_token: $(self).data('csrf'),
                reg_json: JSON.stringify(reg_json)
            }
        }).done(function (json) {
            stop_loading();
            if (json.status === 'ok') {
                swal("Good Job!", "Poof! Metadata of dataset (" + json.reg_info.record_id + ") on Data Catalog has been changed!", "success");
            }else{
                swal("Error Occurred!", "Can not register dataset info!", "error");
            }
        })

    })
    $('.run-btn').on('click',function (event) {
        event.preventDefault();   
        let command = $(this).data('command');
        let self = this;
        swal({
          title: "Are you sure?",
          text: "This action will overwrite the database and may redownload files, are you sure?",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
        .then((willQueue) => {
          if (willQueue) {
            start_loading();
            $.ajax({
                url: '/bash/run',
                type: 'POST',
                dataType: 'json',
                data: {
                    command:command, 
                    csrf_token:$(self).data('csrf'),
                    bashid:$(self).data('bashid')
                }
            }).done(function (json) {
                stop_loading();
                if (json.status == 'queued') {
                    swal("Good Job!", "Poof! Your job has been queued!", "success");    
                }else{
                    swal("Error Occurred!", "You job has not been queued!", "error");
                }
                updateStatus();
            });
          } else {
            swal("Your record did not run!");
          }
        });
    });
    $('.cancel-btn').on('click',function (event) {
        event.preventDefault();
        let self = this;
        swal({
          title: "Are you sure?",
          text: "This action will cancel this job, are you sure?",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
        .then((willCancel) => {
          if (willCancel) {
            start_loading();
            $.ajax({
                url: '/bash/cancel',
                type: 'POST',
                dataType: 'json',
                data: { 
                    csrf_token: $(self).data('csrf'),
                    bashid: $(self).data('bashid')
                }
            }).done(function (json) {
                stop_loading()
                if (json.status == 'Job cancelled') {
                    swal("Good Job!", "Poof! Your job has been canceled!", "success");    
                }else{
                    swal("Error Occurred!", "You job has not been canceled!\n" + json.status, "error");
                }
                updateStatus();
            });
          } else {
            swal("Your job did not be canceled!");
          }
        });
    });
    $('.unregister-btn').on('click',function (event) {
        event.preventDefault();
        let self = this;
        swal({
          title: "Are you sure?",
          text: "This action will let you mark data catalog visualized as registered or unregistered",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
        .then((willUnreg) => {
          if (willUnreg) {
            start_loading();
            $.ajax({
                url: '/bash/unregister',
                type: 'POST',
                dataType: 'json',
                data: { 
                    csrf_token: $(self).data('csrf'),
                    dataset_id: $(self).data('dataset_id'),
                    viz_config: $(self).data('viz_config'),
                    option: $(self).data('option')
                }
            }).done(function (json) {
                stop_loading()
                if (json.status == 'success') {
                    swal("Good Job!", "Poof! The record has been registered/unregistered on Data Catalog!", "success");    
                }else{
                    swal("Error Occurred!", "The record does not registered/unregistered on Data Catalog!", "error");
                }
                updateStatus();
            });
          } else {
            swal("Your record is not changed!");
          }
        });
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
                if(json.status[i] in {'running':0, 'downloading':0}){
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
    $('.status-btn').on('click',function(event){
        event.preventDefault();
        start_loading();
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{
                jobid: $(this).data('rqid'),
                bashid: $(this).data('bashid'),
                download_id: $(this).data('download-id'),
                after_run_ids: $(this).data('after-run-ids'),
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
            stop_loading();
            $('#bash-modal').modal('show');
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
