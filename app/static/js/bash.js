$(document).ready(function () {
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
            data: {command:command, csrf_token:$('.run-btn').data('csrf'),bashid:$('.run-btn').data('bashid')}
        }).done(function (json) {
            window.location.reload();
        });
    });

});


