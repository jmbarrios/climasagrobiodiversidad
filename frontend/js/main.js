$(function() {

	function createCultivoCard(cultivo) {
		const card = document.createElement('div');
		card.className = 'border imagenesMaices col-lg-2 col-md-4 col-sm-6 col-6';

		const link = document.createElement('a');
		link.href = `https://app-siagro.conabio.gob.mx/id=${encodeURIComponent(cultivo.id)}`;
		link.target = '_blank';
		link.rel = 'noopener noreferrer';

		const image = document.createElement('img');
		image.src = cultivo.image;
		image.alt = cultivo.name;
		image.className = 'images';
		link.appendChild(image);

		const label = document.createElement('div');
		label.className = 'bottom-center';
		label.textContent = cultivo.name;

		card.append(link, label);
		return card;
	}

	async function loadCultivos() {
		const response = await fetch('data/cultivos.json');
		if (!response.ok) {
			throw new Error(`No se pudo cargar el catálogo (${response.status})`);
		}

		const catalog = await response.json();
		document.getElementById('maices-list').replaceChildren(
			...catalog.maices.map(createCultivoCard)
		);
		document.getElementById('teocintles-list').replaceChildren(
			...catalog.teocintles.map(createCultivoCard)
		);
	}

	loadCultivos().catch((error) => {
		console.error(error);
	});

  var siteSticky = function() {
		$(".js-sticky-header").sticky({topSpacing:0});
	};
	siteSticky();

	var siteMenuClone = function() {

		$('.js-clone-nav').each(function() {
			var $this = $(this);
			$this.clone().attr('class', 'site-nav-wrap').appendTo('.site-mobile-menu-body');
		});


		setTimeout(function() {
			
			var counter = 0;
      $('.site-mobile-menu .has-children').each(function(){
        var $this = $(this);
        
        $this.prepend('<span class="arrow-collapse collapsed">');

        $this.find('.arrow-collapse').attr({
          'data-toggle' : 'collapse',
          'data-target' : '#collapseItem' + counter,
        });

        $this.find('> ul').attr({
          'class' : 'collapse',
          'id' : 'collapseItem' + counter,
        });

        counter++;

      });

    }, 1000);

		$('body').on('click', '.arrow-collapse', function(e) {
      var $this = $(this);
      if ( $this.closest('li').find('.collapse').hasClass('show') ) {
        $this.removeClass('active');
      } else {
        $this.addClass('active');
      }
      e.preventDefault();  
      
    });

		$(window).resize(function() {
			var $this = $(this),
				w = $this.width();

			if ( w > 768 ) {
				if ( $('body').hasClass('offcanvas-menu') ) {
					$('body').removeClass('offcanvas-menu');
				}
			}
		})

		$('body').on('click', '.js-menu-toggle', function(e) {
			var $this = $(this);
			e.preventDefault();

			if ( $('body').hasClass('offcanvas-menu') ) {
				$('body').removeClass('offcanvas-menu');
				$this.removeClass('active');
			} else {
				$('body').addClass('offcanvas-menu');
				$this.addClass('active');
			}
		}) 

		// click outisde offcanvas
		$(document).mouseup(function(e) {
	    var container = $(".site-mobile-menu");
	    if (!container.is(e.target) && container.has(e.target).length === 0) {
	      if ( $('body').hasClass('offcanvas-menu') ) {
					$('body').removeClass('offcanvas-menu');
				}
	    }
		});
	}; 
	siteMenuClone();

});