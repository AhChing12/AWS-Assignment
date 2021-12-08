$(document).ready(function(){
	/* Initialize all popover */
	$(function () {
		$('[data-toggle="popover"]').popover()
	});

	/* Show confirmation dialog when delete button is clicked */
	$(document).on("click","input.delete-btn",function(){
		//get employee id
		var employeeId = $(this).val();

		//get delete confirmation from user
		var confirmDelete = confirm("Confirm to delete student? ID: "+employeeId);
		event.preventDefault()
		if(confirmDelete === true){
			//send xml request to delete member
			$.ajax({
				url:'/deleteEmp',
				type: "POST",
				data :{"delete":"true", "employee_id":employeeId},
				/* display delete result after recieved xml response */
				// [ Ajax responses ]
				// 0 - Student_id does not exists
				// 1 - Deletion successful
				// 2 - Error occured
				success:function(data){
					switch (data.responses) {
						case '0':
							alert("Member does not exist");
							break;
						case '1':
							$("tr#"+employeeId).fadeOut(1000);
							console.log('Deleted: '+employeeId);
							break;
						case '2':
							alert("Sorry, something went wrong");
							break;
						default:
							console.log('Something went wrong');
							break;
					}
				}
			});
		}
	});
	

});



