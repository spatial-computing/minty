!(function () {
    let pre_tbody;
    $( document ).ready(function() {
        console.log( "ready!" );
        pre_tbody = $('.after-search').clone()
    });
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

    $('body').on('click','.edit-register-metadata', function (event) {
        event.preventDefault();
        let self = this;
        start_loading();
        $.ajax({
            url: '/bash/edit_dc_metadata',
            type: 'POST',
            dataType: 'json',
            data: {
                csrf_token: $('#csrf_token_hidden').val(),
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
    $('body').on('click', '#jsoneditor-modal .save-changes', function (event) {
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
                csrf_token: $(self).val(),
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
    $('body').on('click','.run-btn',function (event) {
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
                    csrf_token:$('#csrf_token_hidden').val(),
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
    $('body').on('click','.cancel-btn',function (event) {
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
                    csrf_token: $('#csrf_token_hidden').val(),
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
    $('body').on('click','.unregister-btn',function (event) {
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
                    csrf_token: $('#csrf_token_hidden').val(),
                    dataset_id: $(self).data('dataset_id'),
                    viz_config: $(self).data('viz_config'),
                    option: $(self).data('option')
                }
            }).done(function (json) {
                stop_loading();
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

                var newWidth = "width:" + json.progress[i] + ";";
                //console.log(newWidth);
                $($(document).find('.progress-bar span')[i]).text(json.progress[i])
                $($(document).find('.progress-bar')[i]).attr("style", newWidth);
            }
            
        });
    }
    updateStatus();
    var handle = setInterval(function () {
        updateStatus();
    }, 10000);
    function escape_html(string) {
        if (typeof(string) === "string") {
            return string.replace(/&/g, "&amp;").replace(/>/g, "&gt;").replace(/</g, "&lt;").replace(/"/g, "&quot;");    
        }
        return "";
    }
    $('body').on('click','.status-btn',function(event){
        event.preventDefault();
        start_loading();
        console.log($(this).data('rqid'));
        console.log("aaaa");
        $.ajax({
            url:'/bash/status',
            type:'POST',
            dataType:'json',
            data:{
                jobid: $(this).data('rqid'),
                bashid: $(this).data('bashid'),
                download_id: $(this).data('download-id'),
                after_run_ids: $(this).data('after-run-ids'),
                csrf_token: $('#csrf_token_hidden').val()
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
    $('body').on('change','.custom-setting',function(event){
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
    $('body').on('change','.custom-controller', function(event){
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

    $('body').on('click', '#clear-search-bar', function (event) {
        event.preventDefault();
        $('#search-bash').val('');
        $('#search-bash').trigger('input');
        $(this).css('visibility', 'hidden');
    });
    $('body').on('input', '#search-bash',function(event){
        event.preventDefault();
        let value = $(this).val()
        if(value.length>=3){
            $('#clear-search-bar').css('visibility', 'visible');
            let csrf_token = $('#csrf_token_hidden').val();
            $.ajax({
                url:'/bash/search',
                type:'POST',
                dataType:'json',
                data:{csrf_token:csrf_token, value:value}
            }).done(function(json){
                    console.log(json.result)
                    $('tbody').remove()
                    $('table').append("<tbody class=\"after-search\"></tbody>")
                    let bash_rqids = []
                    let bash_ids = []
                    json.result.map(bash=>{
                        let {id, command, rqids, viz_config, viz_type, file_type, md5vector, download_ids, after_run_ids, dataset_id} = bash
                        bash_rqids.push(rqids)
                        bash_ids.push(id)
                        let html_string = "\
                        <tr> \
                            <td class=\"bash-status vcenter\"></td>\
                            <td><pre>"+command+"</pre></td>\
                            <td class=\"center\">\
                                <button class=\"btn btn-outline-danger btn-sm run-btn\" data-command= \"" + command + "\" data-bashid=\"" +id+ "\" style=\"display:none\">Run</button>\
                                <button class=\"btn btn-outline-danger btn-sm cancel-btn\" data-command= \""+ command+ "\" data-bashid=\""+id+ "\" style=\"display:none\">Cancel</button>\
                            </td>\
                            <td class=\"center\">\
                                <button class=\"btn btn-outline-info btn-sm status-btn\"  data-rqid=\"" + rqids + "\" data-download-id=\""+download_ids+"\" data-after-run-ids=\"" +after_run_ids+ "\" data-bashid=\""+id+"\" >Log</button>\
                            </td>\
                            <td class=\"center\">\
                                <a class=\"btn btn-outline-primary btn-sm\" href='#' data-href='/bash/edit/"+id+"'>Edit</a>\
                            </td>\
                            <td class='center dc-action'>\
                                <button type='button' class='btn btn-outline-dark btn-sm edit-register-metadata' data-dataset-id=\""+id+"\" data-viz-config=\""+viz_config+"\" >\
                                    Edit DC Metadata\
                                </button>\
                                <button class='btn btn-outline-dark btn-sm unregister-btn' data-dataset_id=\""+id+"\" data-viz_config=\""+viz_config+"\" data-option='False'>Unreg</button>\
                                <button class='btn btn-outline-dark btn-sm unregister-btn' data-dataset_id=\""+id+"\" data-viz_config=\""+viz_config+"\" data-option='True'>Reg</button>\
                            </td>\
                        </tr>"
                        $('tbody').append(html_string)
                    })
                    html_string_bash_rqids = "<input id='bash_rqids' type='hidden' name='rqids' value=\""+bash_rqids.join(',')+"\">"
                    html_string_bash_ids = "<input id='bash_ids' type='hidden' name='bashids' value=\""+ bash_ids.join(',')+"\">"
                    $('tbody').append(html_string_bash_rqids)
                    $('tbody').append(html_string_bash_ids)
                })
            }
        else {
            $('#clear-search-bar').css('visibility', 'hidden');
            $('tbody').remove()
            $('table').append(pre_tbody)
        }
        updateStatus();
    })

    $( document ).ajaxError(function() {
      stop_loading();
    });
}());
